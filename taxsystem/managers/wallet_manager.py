# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.decorators import log_timing
from taxsystem.errors import DatabaseError
from taxsystem.providers import esi
from taxsystem.task_helpers.etag_helpers import etag_results

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.tax import OwnerAudit
    from taxsystem.models.wallet import (
        CorporationWalletDivision,
    )

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationWalletQuerySet(models.QuerySet):
    pass


class CorporationWalletManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "OwnerAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a wallet journal entry from ESI data."""
        return owner.update_section_if_changed(
            section=owner.UpdateSection.WALLET,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(self, owner: "OwnerAudit", force_refresh: bool = False) -> None:
        """Fetch wallet journal entries from ESI data."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.wallet import CorporationWalletDivision

        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions = CorporationWalletDivision.objects.filter(corporation=owner)

        for division in divisions:
            division: CorporationWalletDivision

            current_page = 1
            total_pages = 1
            while current_page <= total_pages:
                journal_items_ob = esi.client.Wallet.get_corporations_corporation_id_wallets_division_journal(
                    corporation_id=owner.corporation.corporation_id,
                    division=division.division_id,
                    page=current_page,
                )
                journal_items = etag_results(
                    journal_items_ob, token, force_refresh=force_refresh
                )

                self._update_or_create_objs(division, journal_items)
                current_page += 1

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        division: "CorporationWalletDivision",
        objs: list,
    ) -> None:
        """Update or Create wallet journal entries from objs data."""
        _new_names = []
        _current_journal = set(
            list(
                self.filter(division=division)
                .order_by("-date")
                .values_list("entry_id", flat=True)[:20000]
            )
        )
        _current_eve_ids = set(
            list(EveEntity.objects.all().values_list("id", flat=True))
        )

        items = []
        for item in objs:
            if item.get("id") not in _current_journal:
                if item.get("second_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("second_party_id"))
                    _current_eve_ids.add(item.get("second_party_id"))
                if item.get("first_party_id") not in _current_eve_ids:
                    _new_names.append(item.get("first_party_id"))
                    _current_eve_ids.add(item.get("first_party_id"))

                wallet_item = self.model(
                    division=division,
                    amount=item.get("amount"),
                    balance=item.get("balance"),
                    context_id=item.get("context_id"),
                    context_id_type=item.get("context_id_type"),
                    date=item.get("date"),
                    description=item.get("description"),
                    first_party_id=item.get("first_party_id"),
                    entry_id=item.get("id"),
                    reason=item.get("reason"),
                    ref_type=item.get("ref_type"),
                    second_party_id=item.get("second_party_id"),
                    tax=item.get("tax"),
                    tax_receiver_id=item.get("tax_receiver_id"),
                )

                items.append(wallet_item)

        # Create Entities
        EveEntity.objects.bulk_resolve_ids(_new_names)
        # Check if created
        all_exist = EveEntity.objects.filter(id__in=_new_names).count() == len(
            _new_names
        )

        if all_exist:
            self.bulk_create(items)
        else:
            raise DatabaseError("DB Fail")


CorporationWalletManager = CorporationWalletManagerBase.from_queryset(
    CorporationWalletQuerySet
)


class CorporationDivisionQuerySet(models.QuerySet):
    pass


class CorporationDivisionManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "OwnerAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return owner.update_section_if_changed(
            section=owner.UpdateSection.DIVISION,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    @log_timing(logger)
    def update_or_create_esi_names(
        self, owner: "OwnerAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return owner.update_section_if_changed(
            section=owner.UpdateSection.DIVISION_NAMES,
            fetch_func=self._fetch_esi_data_names,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data_names(
        self, owner: "OwnerAudit", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        division_obj = esi.client.Corporation.get_corporations_corporation_id_divisions(
            corporation_id=owner.corporation.corporation_id,
        )

        division_names = etag_results(division_obj, token, force_refresh=force_refresh)

        self._update_or_create_objs_division(owner, division_names)

    def _fetch_esi_data(self, owner: "OwnerAudit", force_refresh: bool = False) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions_items_obj = esi.client.Wallet.get_corporations_corporation_id_wallets(
            corporation_id=owner.corporation.corporation_id
        )

        division_balances = etag_results(
            divisions_items_obj, token, force_refresh=force_refresh
        )
        self._update_or_create_objs(owner, division_balances)

    @transaction.atomic()
    def _update_or_create_objs_division(
        self,
        owner: "OwnerAudit",
        objs: list,
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs.get("wallet"):
            if division.get("division") == 1:
                name = _("Master Wallet")
            else:
                name = division.get("name", _("Unknown"))

            obj, created = self.get_or_create(
                corporation=owner,
                division_id=division.get("division"),
                defaults={"balance": 0, "name": name},
            )
            if not created:
                obj.name = name
                obj.save()

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        owner: "OwnerAudit",
        objs: list,
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:
            obj, created = self.get_or_create(
                corporation=owner,
                division_id=division.get("division"),
                defaults={
                    "balance": division.get("balance"),
                    "name": _("Unknown"),
                },
            )

            if not created:
                obj.balance = division.get("balance")
                obj.save()


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)

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

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.tax import OwnerAudit
    from taxsystem.models.wallet import (
        CorporationWalletDivision,
    )

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationJournalContext:
    """Context for corporation wallet journal ESI operations."""

    amount: float
    balance: float
    context_id: int
    context_id_type: str
    date: str
    description: str
    first_party_id: int
    id: int
    reason: str
    ref_type: str
    second_party_id: int
    tax: float
    tax_receiver_id: int


class CorporationDivisionContext:
    class WalletContext:
        division: int
        name: str | None

    class HangerContext:
        division: int
        name: str | None

    hanger: list[HangerContext]
    wallet: list[WalletContext]


class CorporationWalletContext:
    division: int
    balance: float


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

    # pylint: disable=too-many-locals
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
            journal_items_ob = (
                esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                    corporation_id=owner.corporation.corporation_id,
                    division=division.division_id,
                    token=token,
                )
            )
            logger.debug(
                "Fetching Journal Items for %s - Division: %s - Page: %s/%s",
                owner.corporation.corporation_name,
                division.division_id,
            )

            objs, __ = journal_items_ob.results(return_response=True)

            if force_refresh:
                pass  # TODO Make new Etag Checker

            self._update_or_create_objs(division=division, objs=objs)

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        division: "CorporationWalletDivision",
        objs: list[CorporationJournalContext],
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
            if item.id not in _current_journal:
                if item.second_party_id not in _current_eve_ids:
                    _new_names.append(item.second_party_id)
                    _current_eve_ids.add(item.second_party_id)
                if item.first_party_id not in _current_eve_ids:
                    _new_names.append(item.first_party_id)
                    _current_eve_ids.add(item.first_party_id)

                wallet_item = self.model(
                    division=division,
                    amount=item.amount,
                    balance=item.balance,
                    context_id=item.context_id,
                    context_id_type=item.context_id_type,
                    date=item.date,
                    description=item.description,
                    first_party_id=item.first_party_id,
                    entry_id=item.id,
                    reason=item.reason,
                    ref_type=item.ref_type,
                    second_party_id=item.second_party_id,
                    tax=item.tax,
                    tax_receiver_id=item.tax_receiver_id,
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

        division_obj = esi.client.Corporation.GetCorporationsCorporationIdDivisions(
            corporation_id=owner.corporation.corporation_id, token=token
        )

        objs, __ = division_obj.results(return_response=True)

        if force_refresh:
            pass  # TODO Make new Etag Checker

        self._update_or_create_objs_division(owner=owner, objs=objs)

    def _fetch_esi_data(self, owner: "OwnerAudit", force_refresh: bool = False) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        divisions_items_obj = esi.client.Wallet.GetCorporationsCorporationIdWallets(
            corporation_id=owner.corporation.corporation_id, token=token
        )

        objs, __ = divisions_items_obj.results(return_response=True)
        if force_refresh:
            pass  # TODO Make new Etag Checker

        self._update_or_create_objs(owner=owner, objs=objs)

    @transaction.atomic()
    def _update_or_create_objs_division(
        self,
        owner: "OwnerAudit",
        objs: list[CorporationDivisionContext],
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:  # list (hanger, wallet)
            for wallet_data in division.wallet:
                obj, created = self.get_or_create(
                    corporation=owner,
                    division_id=wallet_data.division,
                    defaults={
                        "balance": 0,
                        "name": wallet_data.name if wallet_data.name else _("Unknown"),
                    },
                )
                if not created:
                    obj.name = wallet_data.name
                    obj.save()

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        owner: "OwnerAudit",
        objs: list[CorporationWalletContext],
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:
            obj, created = self.get_or_create(
                corporation=owner,
                division_id=division.division,
                defaults={
                    "balance": division.balance,
                    "name": _("Unknown"),
                },
            )

            if not created:
                obj.balance = division.balance
                obj.save()


CorporationDivisionManager = CorporationDivisionManagerBase.from_queryset(
    CorporationDivisionQuerySet
)

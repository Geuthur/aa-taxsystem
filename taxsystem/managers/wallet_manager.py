# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.app_settings import TAXSYSTEM_BULK_BATCH_SIZE
from taxsystem.decorators import log_timing
from taxsystem.errors import DatabaseError
from taxsystem.models.helpers.textchoices import CorporationUpdateSection
from taxsystem.providers import esi

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.corporation import CorporationOwner
    from taxsystem.models.wallet import (
        CorporationWalletDivision,
        CorporationWalletJournalEntry,
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


class CorporationWalletManager(models.Manager["CorporationWalletJournalEntry"]):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a wallet journal entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.WALLET,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    # pylint: disable=too-many-locals
    def _fetch_esi_data(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
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
        is_updated = False

        for division in divisions:
            # Make the ESI request
            journal_items_ob = (
                esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                    corporation_id=owner.eve_corporation.corporation_id,
                    division=division.division_id,
                    token=token,
                )
            )

            try:
                journal_items, response = journal_items_ob.results(
                    return_response=True, force_refresh=force_refresh
                )
                is_updated = True
                logger.debug("ESI response Status: %s", response.status_code)
            except HTTPNotModified:
                continue

            self._update_or_create_objs(division=division, objs=journal_items)
        # Raise if no update happened at all
        if not is_updated:
            raise HTTPNotModified(304, {"msg": "Wallet Journal has Not Modified"})

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
            self.bulk_create(items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE)
        else:
            raise DatabaseError("DB Fail")


class CorporationDivisionManager(models.Manager["CorporationWalletDivision"]):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.DIVISIONS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    @log_timing(logger)
    def update_or_create_esi_names(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a division entry from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.DIVISION_NAMES,
            fetch_func=self._fetch_esi_data_names,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data_names(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director"]
        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        # Make the ESI request
        division_names_obj = (
            esi.client.Corporation.GetCorporationsCorporationIdDivisions(
                corporation_id=owner.eve_corporation.corporation_id, token=token
            )
        )
        division_names_items, response = division_names_obj.results(
            return_response=True, force_refresh=force_refresh
        )
        logger.debug("ESI response Status: %s", response.status_code)

        self._update_or_create_objs_division(owner=owner, objs=division_names_items)

    def _fetch_esi_data(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Fetch division entries from ESI data."""
        req_scopes = [
            "esi-wallet.read_corporation_wallets.v1",
            "esi-characters.read_corporation_roles.v1",
            "esi-corporations.read_divisions.v1",
        ]
        req_roles = ["CEO", "Director", "Accountant", "Junior_Accountant"]
        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        # Make the ESI request
        divisions_items_obj = esi.client.Wallet.GetCorporationsCorporationIdWallets(
            corporation_id=owner.eve_corporation.corporation_id, token=token
        )
        division_items, response = divisions_items_obj.results(
            return_response=True, force_refresh=force_refresh
        )
        logger.debug("ESI response Status: %s", response.status_code)

        self._update_or_create_objs(owner=owner, objs=division_items)

    @transaction.atomic()
    def _update_or_create_objs_division(
        self,
        owner: "CorporationOwner",
        objs: list[CorporationDivisionContext],
    ) -> None:
        """Update or Create division entries from objs data."""
        for division in objs:  # list (hanger, wallet)
            for wallet_data in division.wallet:
                if wallet_data.division == 1:
                    name = _("Master Wallet")
                else:
                    name = getattr(wallet_data, "name", _("Unknown"))

                obj, created = self.get_or_create(
                    corporation=owner,
                    division_id=wallet_data.division,
                    defaults={
                        "balance": 0,
                        "name": name,
                    },
                )
                if not created:
                    obj.name = name
                    obj.save()

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        owner: "CorporationOwner",
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

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.decorators import log_timing
from taxsystem.managers.base import BaseOwnerQuerySet
from taxsystem.models.general import CorporationUpdateSection
from taxsystem.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.corporation import CorporationOwner


class CorporationMemberTrackingContext:
    """Context for corporation member tracking ESI operations."""

    base_id: int
    character_id: int
    location_id: int
    logoff_date: timezone.datetime
    logon_date: timezone.datetime
    ship_type_id: int
    start_date: timezone.datetime


class CorporationOwnerQuerySet(BaseOwnerQuerySet):
    """QuerySet for CorporationOwner with common filtering logic."""

    # Configure base class for corporation-specific behavior
    owner_type = "corp"
    permission_prefix = "taxsystem.manage_corps"
    owner_field = "corporation_id"  # Field on EveCharacter
    owner_model_field = (
        "eve_corporation__corporation_id"  # Field on CorporationOwner model
    )
    own_permission = "taxsystem.manage_own_corp"
    update_status_relation = "ts_corporation_update_status"
    update_section_class = CorporationUpdateSection

    def annotate_total_update_status_user(self, user):
        """Get the total update status for the given user."""
        char = user.profile.main_character
        assert char

        query = models.Q(character__character_ownership__user=user)

        return self.filter(query).annotate_total_update_status()

    def disable_characters_with_no_owner(self) -> int:
        """Disable characters which have no owner. Return count of disabled characters."""
        orphaned_characters = self.filter(
            character__character_ownership__isnull=True, active=True
        )
        if orphaned_characters.exists():
            orphans = list(
                orphaned_characters.values_list(
                    "character__character_name", flat=True
                ).order_by("character__character_name")
            )
            orphaned_characters.update(active=False)
            logger.info(
                "Disabled %d characters which do not belong to a user: %s",
                len(orphans),
                ", ".join(orphans),
            )
            return len(orphans)
        return 0


class CorporationOwnerManager(models.Manager):
    def get_queryset(self):
        return CorporationOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


class MembersManager(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a Members from ESI data."""
        return owner.update_section_if_changed(
            section=CorporationUpdateSection.MEMBERS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Fetch Members entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_corporation_membership.v1",
            "esi-corporations.track_members.v1",
        ]
        req_roles = ["CEO", "Director"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        # Check Payment Accounts
        self._check_payment_accounts(owner)

        # Make the ESI request
        members_ob = esi.client.Corporation.GetCorporationsCorporationIdMembertracking(
            corporation_id=owner.eve_corporation.corporation_id,
            token=token,
        )

        members_items, response = members_ob.results(
            return_response=True, force_refresh=force_refresh
        )
        logger.debug("ESI response Status: %s", response.status_code)

        self._update_or_create_objs(owner=owner, objs=members_items)

    @transaction.atomic()
    # pylint: disable=too-many-locals
    def _update_or_create_objs(
        self,
        owner: "CorporationOwner",
        objs: list[CorporationMemberTrackingContext],
    ) -> None:
        """Update or Create Members entries from objs data."""
        logger.info("Updating Members for: %s", owner.name)

        _current_members_ids = set(
            self.filter(owner=owner).values_list("character_id", flat=True)
        )
        _esi_members_ids = [member.character_id for member in objs]
        _old_members = []
        _new_members = []

        characters = EveEntity.objects.bulk_resolve_names(_esi_members_ids)
        for member in objs:
            character_id = member.character_id
            joined = member.start_date
            logon_date = member.logon_date
            logged_off = member.logoff_date
            character_name = characters.to_name(character_id)
            member_item = self.model(
                owner=owner,
                character_id=character_id,
                character_name=character_name,
                joined=joined,
                logon=logon_date,
                logged_off=logged_off,
                status=self.model.States.ACTIVE,
            )
            if character_id in _current_members_ids:
                _old_members.append(member_item)
            else:
                _new_members.append(member_item)

        # Set missing members
        old_member_ids = {member.character_id for member in _old_members}
        missing_members_ids = _current_members_ids - old_member_ids

        if missing_members_ids:
            self.filter(owner=owner, character_id__in=missing_members_ids).update(
                status=self.model.States.MISSING
            )
            logger.debug(
                "Marked %s missing members for: %s",
                len(missing_members_ids),
                owner.name,
            )
        if _old_members:
            self.bulk_update(
                _old_members,
                ["character_name", "status", "logon", "logged_off"],
            )
            logger.debug(
                "Updated %s members for: %s",
                len(_old_members),
                owner.name,
            )
        if _new_members:
            self.bulk_create(_new_members, ignore_conflicts=True)
            logger.debug(
                "Added %s new members for: %s",
                len(_new_members),
                owner.name,
            )

        # Update payment accounts
        self._update_payment_accounts(owner, _esi_members_ids)

        logger.info(
            "%s - Old Members: %s, New Members: %s, Missing: %s",
            owner.name,
            len(_old_members),
            len(_new_members),
            len(missing_members_ids),
        )

    def _update_payment_accounts(
        self, owner: "CorporationOwner", members_ids: list[int]
    ):
        """Update payment accounts for a corporation."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.corporation import CorporationPaymentAccount

        logger.debug(
            "Updating Payment Accounts for: %s",
            owner.name,
        )

        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=owner.eve_corporation.corporation_id,
        ).select_related(
            "user__profile__main_character",
            "main_character__character_ownership",
            "main_character__character_ownership__user__profile",
            "main_character__character_ownership__user__profile__main_character",
        )

        members = self.filter(owner=owner)

        if not accounts:
            logger.debug("No valid accounts for: %s", owner.name)
            return "No Accounts"

        items = []

        for account in accounts:
            alts = set(
                account.user.character_ownerships.all().values_list(
                    "character__character_id", flat=True
                )
            )
            main = account.main_character

            # Change the status of members if they are alts
            relevant_alts = alts.intersection(members_ids)
            for alt in relevant_alts:
                members_ids.remove(alt)
                if alt != main.character_id:
                    # Update the status of the member to alt
                    members.filter(character_id=alt).update(
                        status=self.model.States.IS_ALT
                    )

            # Create or update a Payment System for the main character
            try:
                existing_payment_system = CorporationPaymentAccount.objects.get(
                    user=account.user, owner=owner
                )

                if (
                    existing_payment_system.status
                    != CorporationPaymentAccount.Status.DEACTIVATED
                ):
                    existing_payment_system.status = (
                        CorporationPaymentAccount.Status.ACTIVE
                    )
                    existing_payment_system.save()
            except CorporationPaymentAccount.DoesNotExist:
                items.append(
                    CorporationPaymentAccount(
                        name=main.character_name,
                        owner=owner,
                        user=account.user,
                        status=CorporationPaymentAccount.Status.ACTIVE,
                    )
                )

        if members_ids:
            # Mark members without accounts
            for member_id in members_ids:
                members.filter(character_id=member_id).update(
                    status=self.model.States.NOACCOUNT
                )

            logger.debug(
                "Marked %s members without accounts for: %s",
                len(members_ids),
                owner.name,
            )

        if items:
            CorporationPaymentAccount.objects.bulk_create(items, ignore_conflicts=True)
            logger.info(
                "Added %s new payment users for: %s",
                len(items),
                owner.name,
            )
        else:
            logger.debug(
                "No new payment user for: %s",
                owner.name,
            )

        return (
            "Finished payment system for %s",
            owner.name,
        )

    def _check_payment_accounts(self, owner: "CorporationOwner"):
        """Check payment accounts for a corporation."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.corporation import (
            CorporationOwner,
            CorporationPaymentAccount,
        )

        logger.debug(
            "Checking Payment Accounts for: %s",
            owner.name,
        )

        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).select_related(
            "user__profile__main_character",
            "main_character__character_ownership",
            "main_character__character_ownership__user__profile",
            "main_character__character_ownership__user__profile__main_character",
        )

        if not accounts:
            logger.debug(
                "No valid accounts for skipping Check: %s",
                owner.name,
            )
            return "No Accounts"

        for account in accounts:
            main_corporation_id = account.main_character.corporation_id

            try:
                payment_system = CorporationPaymentAccount.objects.get(
                    user=account.user, owner=owner
                )
                payment_system_corp_id = (
                    payment_system.owner.eve_corporation.corporation_id
                )
                # Check if the user is no longer in the same corporation
                if (
                    not payment_system.is_missing
                    and not payment_system_corp_id == main_corporation_id
                ):
                    payment_system.status = CorporationPaymentAccount.Status.MISSING
                    payment_system.save()
                    logger.info(
                        "User %s is no longer in Corp marked as Missing",
                        payment_system.name,
                    )
                # Check if the user changed to a existing corporation Payment System
                elif (
                    payment_system.is_missing
                    and payment_system_corp_id != main_corporation_id
                ):
                    try:
                        new_owner = CorporationOwner.objects.get(
                            eve_corporation__corporation_id=main_corporation_id
                        )
                        payment_system.owner = new_owner
                        payment_system.deposit = 0
                        payment_system.status = CorporationPaymentAccount.Status.ACTIVE
                        payment_system.last_paid = None
                        payment_system.save()
                        logger.info(
                            "User %s is now in Corporation %s",
                            payment_system.name,
                            new_owner.eve_corporation.corporation_name,
                        )
                    except owner.DoesNotExist:
                        continue
                elif (
                    payment_system.is_missing
                    and payment_system_corp_id == main_corporation_id
                ):
                    payment_system.status = CorporationPaymentAccount.Status.ACTIVE
                    payment_system.notice = None
                    payment_system.deposit = 0
                    payment_system.last_paid = None
                    payment_system.save()
                    logger.info(
                        "User %s is back in Corporation %s",
                        payment_system.name,
                        payment_system.owner.eve_corporation.corporation_name,
                    )
            except CorporationPaymentAccount.DoesNotExist:
                logger.debug(
                    "No Payment System for %s - %s",
                    account.user.username,
                    owner.name,
                )
                continue
        return (
            "Finished checking Payment Accounts for %s",
            owner.name,
        )

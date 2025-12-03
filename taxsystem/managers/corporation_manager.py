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
from taxsystem.app_settings import TAXSYSTEM_BULK_BATCH_SIZE
from taxsystem.constants import AUTH_SELECT_RELATED_MAIN_CHARACTER
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


class CorporationOwnerManager(models.Manager["CorporationOwner"]):
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
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
            )
            logger.debug(
                "Updated %s members for: %s",
                len(_old_members),
                owner.name,
            )
        if _new_members:
            self.bulk_create(
                _new_members,
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
                ignore_conflicts=True,
            )
            logger.debug(
                "Added %s new members for: %s",
                len(_new_members),
                owner.name,
            )

        # Update Members
        self._update_members(owner, _esi_members_ids)

        logger.info(
            "%s - Old Members: %s, New Members: %s, Missing: %s",
            owner.name,
            len(_old_members),
            len(_new_members),
            len(missing_members_ids),
        )
        return (
            "Finished members update for %s",
            owner.name,
        )

    def _update_members(self, owner: "CorporationOwner", members_ids: list[int]):
        """Update Members for a corporation."""

        auth_accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=owner.eve_corporation.corporation_id,
        ).select_related(*AUTH_SELECT_RELATED_MAIN_CHARACTER)

        members = self.filter(owner=owner)

        if not auth_accounts:
            logger.debug("No valid accounts for: %s", owner.name)
            return "No Accounts"

        for account in auth_accounts:
            # Get all alts for the user
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
                if alt == main.character_id:
                    # Update main character to active if it was previously in another state
                    members.filter(character_id=main.character_id).exclude(
                        status=self.model.States.ACTIVE
                    ).update(status=self.model.States.ACTIVE)
                else:
                    # Update the status of the member to alt
                    members.filter(character_id=alt).update(
                        status=self.model.States.IS_ALT
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
        return "Updated Members statuses for %s", owner.name

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import Case, Count, Q, Value, When

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem import __title__
from taxsystem.decorators import log_timing
from taxsystem.providers import esi
from taxsystem.task_helpers.etag_helpers import etag_results

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.tax import OwnerAudit


class OwnerAuditQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Get all corps visible to the user."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all corps for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_corps"):
            logger.debug("Returning all corps for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            corp_ids = user.character_ownerships.all().values_list(
                "character__corporation_id", flat=True
            )
            queries = [models.Q(corporation__corporation_id__in=corp_ids)]

            logger.debug(
                "%s queries for user %s visible corporations.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user):
        """Get all corps that the user can manage."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all corps for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_corps"):
            logger.debug("Returning all corps for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            query = None

            if user.has_perm("taxsystem.manage_own_corp"):
                query = models.Q(corporation__corporation_id=char.corporation_id)

            logger.debug("Returning own corps for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def annotate_total_update_status_user(self, user):
        """Get the total update status for the given user."""
        char = user.profile.main_character
        assert char

        query = models.Q(character__character_ownership__user=user)

        return self.filter(query).annotate_total_update_status()

    def annotate_total_update_status(self):
        """Get the total update status."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.tax import OwnerAudit

        sections = OwnerAudit.UpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ts_update_status",
                    filter=Q(ts_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ts_update_status",
                    filter=Q(
                        ts_update_status__section__in=sections,
                        ts_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ts_update_status",
                    filter=Q(
                        ts_update_status__section__in=sections,
                        ts_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ts_update_status",
                    filter=Q(
                        ts_update_status__section__in=sections,
                        ts_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(OwnerAudit.UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(OwnerAudit.UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(OwnerAudit.UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(OwnerAudit.UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(OwnerAudit.UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(OwnerAudit.UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs

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


class OwnerAuditManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


OwnerAuditManager = OwnerAuditManagerBase.from_queryset(OwnerAuditQuerySet)


class MembersQuerySet(models.QuerySet):
    pass


class MembersManagerBase(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "OwnerAudit", force_refresh: bool = False
    ) -> None:
        """Update or Create a Members from ESI data."""
        return owner.update_section_if_changed(
            section=owner.UpdateSection.MEMBERS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(self, owner: "OwnerAudit", force_refresh: bool = False) -> None:
        """Fetch Members entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_corporation_membership.v1",
            "esi-corporations.track_members.v1",
        ]
        req_roles = ["CEO", "Director"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        # Check Payment Accounts
        self._check_payment_accounts(owner)

        members_ob = (
            esi.client.Corporation.get_corporations_corporation_id_membertracking(
                corporation_id=owner.corporation.corporation_id,
            )
        )

        members_items = etag_results(members_ob, token, force_refresh=force_refresh)

        self._update_or_create_objs(
            owner,
            members_items,
        )

    @transaction.atomic()
    # pylint: disable=too-many-locals
    def _update_or_create_objs(
        self,
        owner: "OwnerAudit",
        objs: list,
    ) -> None:
        """Update or Create Members entries from objs data."""
        _current_members_ids = set(
            self.filter(owner=owner).values_list("character_id", flat=True)
        )
        _esi_members_ids = [member.get("character_id") for member in objs]
        _old_members = []
        _new_members = []

        characters = EveEntity.objects.bulk_resolve_names(_esi_members_ids)

        for member in objs:
            character_id = member.get("character_id")
            joined = member.get("start_date")
            logon_date = member.get("logon_date")
            logged_off = member.get("logoff_date")
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
                owner.corporation.corporation_name,
            )
        if _old_members:
            self.bulk_update(
                _old_members,
                ["character_name", "status", "logon", "logged_off"],
            )
            logger.debug(
                "Updated %s members for: %s",
                len(_old_members),
                owner.corporation.corporation_name,
            )
        if _new_members:
            self.bulk_create(_new_members, ignore_conflicts=True)
            logger.debug(
                "Added %s new members for: %s",
                len(_new_members),
                owner.corporation.corporation_name,
            )

        # Update payment accounts
        self._update_payment_accounts(owner, _esi_members_ids)

        logger.info(
            "Corp %s - Old Members: %s, New Members: %s, Missing: %s",
            owner.name,
            len(_old_members),
            len(_new_members),
            len(missing_members_ids),
        )

    def _update_payment_accounts(self, owner: "OwnerAudit", members_ids: list[int]):
        """Update payment accounts for a corporation."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.tax import PaymentSystem

        logger.debug(
            "Updating Payment Accounts for: %s",
            owner.corporation.corporation_name,
        )

        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=owner.corporation.corporation_id,
        ).select_related(
            "user__profile__main_character",
            "main_character__character_ownership",
            "main_character__character_ownership__user__profile",
            "main_character__character_ownership__user__profile__main_character",
        )

        members = self.filter(owner=owner)

        if not accounts:
            logger.debug(
                "No valid accounts for: %s", owner.corporation.corporation_name
            )
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
                existing_payment_system = PaymentSystem.objects.get(
                    user=account.user, owner=owner
                )

                if existing_payment_system.status != PaymentSystem.Status.DEACTIVATED:
                    existing_payment_system.status = PaymentSystem.Status.ACTIVE
                    existing_payment_system.save()
            except PaymentSystem.DoesNotExist:
                items.append(
                    PaymentSystem(
                        name=main.character_name,
                        owner=owner,
                        user=account.user,
                        status=PaymentSystem.Status.ACTIVE,
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
                owner.corporation.corporation_name,
            )

        if items:
            PaymentSystem.objects.bulk_create(items, ignore_conflicts=True)
            logger.info(
                "Added %s new payment users for: %s",
                len(items),
                owner.corporation.corporation_name,
            )
        else:
            logger.debug(
                "No new payment user for: %s",
                owner.corporation.corporation_name,
            )

        return (
            "Finished payment system for %s",
            owner.corporation.corporation_name,
        )

    def _check_payment_accounts(self, owner: "OwnerAudit"):
        """Check payment accounts for a corporation."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.tax import OwnerAudit, PaymentSystem

        logger.debug(
            "Checking Payment Accounts for: %s",
            owner.corporation.corporation_name,
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
                owner.corporation.corporation_name,
            )
            return "No Accounts"

        for account in accounts:
            main_corporation_id = account.main_character.corporation_id

            try:
                payment_system = PaymentSystem.objects.get(
                    user=account.user, owner=owner
                )
                payment_system_corp_id = payment_system.owner.corporation.corporation_id
                # Check if the user is no longer in the same corporation
                if (
                    not payment_system.is_missing
                    and not payment_system_corp_id == main_corporation_id
                ):
                    payment_system.status = PaymentSystem.Status.MISSING
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
                        new_owner = OwnerAudit.objects.get(
                            corporation__corporation_id=main_corporation_id
                        )
                        payment_system.owner = new_owner
                        payment_system.deposit = 0
                        payment_system.status = PaymentSystem.Status.ACTIVE
                        payment_system.last_paid = None
                        payment_system.save()
                        logger.info(
                            "User %s is now in Corporation %s",
                            payment_system.name,
                            new_owner.corporation.corporation_name,
                        )
                    except owner.DoesNotExist:
                        continue
                elif (
                    payment_system.is_missing
                    and payment_system_corp_id == main_corporation_id
                ):
                    payment_system.status = PaymentSystem.Status.ACTIVE
                    payment_system.notice = None
                    payment_system.deposit = 0
                    payment_system.last_paid = None
                    payment_system.save()
                    logger.info(
                        "User %s is back in Corporation %s",
                        payment_system.name,
                        payment_system.owner.corporation.corporation_name,
                    )
            except PaymentSystem.DoesNotExist:
                logger.debug(
                    "No Payment System for %s - %s",
                    account.user.username,
                    owner.corporation.corporation_name,
                )
                continue
        return (
            "Finished checking Payment Accounts for %s",
            owner.corporation.corporation_name,
        )


MembersManager = MembersManagerBase.from_queryset(MembersQuerySet)

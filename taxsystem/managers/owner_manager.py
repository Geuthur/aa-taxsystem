# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models import Case, Count, Q, Value, When

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.models.helpers.textchoices import (
    AllianceUpdateSection,
    CorporationUpdateSection,
    UpdateStatus,
)
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.alliance import AllianceOwner
    from taxsystem.models.corporation import CorporationOwner


class CorporationOwnerQuerySet(models.QuerySet["CorporationOwner"]):
    """QuerySet for CorporationOwner with common filtering logic."""

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
            queries = [models.Q(eve_corporation__corporation_id__in=corp_ids)]

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
                query = models.Q(eve_corporation__corporation_id=char.corporation_id)

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
        sections = CorporationUpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ts_corporation_update_status",
                    filter=Q(ts_corporation_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ts_corporation_update_status",
                    filter=Q(
                        ts_corporation_update_status__section__in=sections,
                        ts_corporation_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ts_corporation_update_status",
                    filter=Q(
                        ts_corporation_update_status__section__in=sections,
                        ts_corporation_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ts_corporation_update_status",
                    filter=Q(
                        ts_corporation_update_status__section__in=sections,
                        ts_corporation_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class CorporationOwnerManager(models.Manager["CorporationOwner"]):
    def get_queryset(self):
        return CorporationOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()


class AllianceOwnerQuerySet(models.QuerySet["AllianceOwner"]):
    """QuerySet for AllianceOwner with common filtering logic."""

    def visible_to(self, user):
        """Get all allys visible to the user."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all alliances for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_alliances"):
            logger.debug("Returning all alliances for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            alliance_ids = user.character_ownerships.all().values_list(
                "character__alliance_id", flat=True
            )
            queries = [models.Q(eve_alliance__alliance_id__in=alliance_ids)]

            logger.debug(
                "%s queries for user %s visible alliances.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user):
        """Get all alliances that the user can manage."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all alliances for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_alliances"):
            logger.debug("Returning all alliances for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            query = None

            if user.has_perm("taxsystem.manage_own_alliance"):
                query = models.Q(eve_alliance__alliance_id=char.alliance_id)

            logger.debug("Returning own alliances for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    # pylint: disable=duplicate-code
    def annotate_total_update_status(self):
        """Get the total update status."""
        sections = AllianceUpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ts_alliance_update_status",
                    filter=Q(ts_alliance_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class AllianceOwnerManager(models.Manager["AllianceOwner"]):
    def get_queryset(self):
        return AllianceOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()

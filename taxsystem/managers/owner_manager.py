# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.db.models import Case, Count, Q, Value, When

# AA TaxSystem
from taxsystem.managers.general import GeneralManager
from taxsystem.models.helpers.update_manager import (
    AllianceUpdateSection,
    CorporationUpdateSection,
    UpdateSection,
    UpdateStatus,
)
from taxsystem.providers import logger

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.alliance import AllianceOwner
    from taxsystem.models.corporation import CorporationOwner


class CorporationOwnerQuerySet(models.QuerySet["CorporationOwner"]):
    """QuerySet for CorporationOwner with common filtering logic."""

    def visible_to(self, user):
        """Get all corps visible to the user."""
        if GeneralManager.has_manage_corps_access(user):
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
        if GeneralManager.has_manage_corps_access(user):
            logger.debug("Returning all corps for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            query = None

            if GeneralManager.has_manage_own_corp_access(user):
                query = models.Q(eve_corporation__corporation_id=char.corporation_id)

            logger.debug("Returning own corps for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class CorporationOwnerManager(models.Manager["CorporationOwner"]):
    def get_queryset(self):
        return CorporationOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


class AllianceOwnerQuerySet(models.QuerySet["AllianceOwner"]):
    """QuerySet for AllianceOwner with common filtering logic."""

    def visible_to(self, user):
        """Get all allys visible to the user."""
        if GeneralManager.has_manage_alliances_access(user):
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
        if GeneralManager.has_manage_alliances_access(user):
            logger.debug("Returning all alliances for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            query = None

            if GeneralManager.has_manage_own_alliance_access(user):
                query = models.Q(eve_alliance__alliance_id=char.alliance_id)

            logger.debug("Returning own alliances for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()


class AllianceOwnerManager(models.Manager["AllianceOwner"]):
    def get_queryset(self):
        return AllianceOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


class UpdateStatusQuerySet(models.QuerySet):
    """
    QuerySet of an update status model (one row per owner and section).

    Subclasses set `update_section_class` to the sections of their owner.
    """

    update_section_class: type[UpdateSection]

    def get_status(self) -> UpdateStatus:
        """Return the current aggregate update status."""
        total_update_status = (
            self.annotate_total_update_status()
            .values_list("total_update_status", flat=True)
            .order_by("total_update_status")
            .first()
        )

        if total_update_status is None:
            return UpdateStatus.INCOMPLETE
        return UpdateStatus(total_update_status)

    def annotate_total_update_status(self):
        """Annotate one aggregate status per owner over all sections."""
        sections = self.update_section_class.get_sections()
        total_sections = len(sections)
        qs = (
            self.values("owner_id", "owner__active")
            .annotate(num_sections_found=Count("pk", filter=Q(section__in=sections)))
            .annotate(
                num_sections_ok=Count(
                    "pk", filter=Q(section__in=sections, is_success=True)
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "pk", filter=Q(section__in=sections, is_success=False)
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "pk", filter=Q(section__in=sections, has_token_error=True)
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(owner__active=False, then=Value(UpdateStatus.DISABLED)),
                    When(
                        num_sections_token_error__gt=0,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(num_sections_failed__gt=0, then=Value(UpdateStatus.ERROR)),
                    When(num_sections_ok=total_sections, then=Value(UpdateStatus.OK)),
                    When(
                        num_sections_found__lt=total_sections,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class CorporationUpdateStatusQuerySet(UpdateStatusQuerySet):
    update_section_class = CorporationUpdateSection


class AllianceUpdateStatusQuerySet(UpdateStatusQuerySet):
    update_section_class = AllianceUpdateSection


class UpdateStatusManager(models.Manager):
    """Manager of an update status model; `queryset_class` sets the sections."""

    queryset_class: type[UpdateStatusQuerySet]

    def get_queryset(self):
        return self.queryset_class(model=self.model, using=self._db)

    def get_status(self) -> UpdateStatus:
        """Return the current aggregate update status."""
        return self.get_queryset().get_status()

    def annotate_total_update_status(self):
        """Annotate one aggregate status per owner over all sections."""
        return self.get_queryset().annotate_total_update_status()


class CorporationUpdateStatusManager(UpdateStatusManager):
    queryset_class = CorporationUpdateStatusQuerySet


class AllianceUpdateStatusManager(UpdateStatusManager):
    queryset_class = AllianceUpdateStatusQuerySet

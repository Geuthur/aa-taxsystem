# Standard Library
from typing import Generic, TypeVar

# Django
from django.db import models
from django.db.models import Count, Q

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

# Type variable for Owner model
T = TypeVar("T", bound=models.Model)


class BaseOwnerQuerySet(models.QuerySet, Generic[T]):
    """
    Base QuerySet for Owner models (Corporation/Alliance).

    Provides common filtering logic for visibility and management permissions.
    Generic implementation that works for both CorporationOwner and AllianceOwner.
    """

    # Subclasses must define these
    owner_type: str  # "corp" or "alliance"
    permission_prefix: str  # "taxsystem.manage_corps" or "taxsystem.manage_alliances"
    owner_field: str  # "corporation_id" or "alliance_id" (on EveCharacter)
    owner_model_field: str  # "eve_corporation__corporation_id" or "eve_alliance__alliance_id" (on Owner model)
    own_permission: (
        str  # "taxsystem.manage_own_corp" or "taxsystem.manage_own_alliance"
    )
    update_status_relation: (
        str  # "ts_corporation_update_status" or "ts_alliance_update_status"
    )
    update_section_class: type  # CorporationUpdateSection or AllianceUpdateSection

    def visible_to(self, user: User):
        """
        Get all owners visible to the user.

        Visibility rules:
        - Superusers see all
        - Users with manage permission see all
        - Regular users see owners where they have characters

        Args:
            user: Django user object

        Returns:
            Filtered queryset of owners visible to the user
        """
        # Superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all %ss for superuser %s.",
                self.owner_type,
                user,
            )
            return self

        # Users with manage permission get all visible
        if user.has_perm(self.permission_prefix):
            logger.debug(
                "Returning all %ss for Tax Audit Manager %s.", self.owner_type, user
            )
            return self

        # Regular users see owners where they have characters
        try:
            char = user.profile.main_character
            assert char
            owner_ids = user.character_ownerships.all().values_list(
                f"character__{self.owner_field}", flat=True
            )
            queries = [models.Q(**{f"{self.owner_model_field}__in": owner_ids})]

            logger.debug(
                "%s queries for user %s visible %ss.",
                len(queries),
                user,
                self.owner_type,
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user: User):
        """
        Get all owners that the user can manage.

        Management rules:
        - Superusers can manage all
        - Users with manage permission can manage all
        - Users with manage_own permission can manage their own owner

        Args:
            user: Django user object

        Returns:
            Filtered queryset of owners the user can manage
        """
        # Superusers get all
        if user.is_superuser:
            logger.debug(
                "Returning all %ss for superuser %s.",
                self.owner_type,
                user,
            )
            return self

        # Users with manage permission get all
        if user.has_perm(self.permission_prefix):
            logger.debug(
                "Returning all %ss for Tax Audit Manager %s.", self.owner_type, user
            )
            return self

        # Users with own permission get their own
        try:
            char = user.profile.main_character
            assert char
            query = None

            if user.has_perm(self.own_permission):
                # Get the owner_id value from the character
                owner_id = getattr(char, self.owner_field)
                query = models.Q(**{self.owner_model_field: owner_id})

            logger.debug("Returning own %ss for User %s.", self.owner_type, user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def annotate_total_update_status(self):
        """
        Annotate queryset with complete update status information.

        Adds:
        - num_sections_total: Total number of update sections
        - num_sections_ok: Number of successfully updated sections
        - num_sections_failed: Number of failed sections
        - num_sections_token_error: Number of sections with token errors
        - total_update_status: Overall status (DISABLED, TOKEN_ERROR, ERROR, OK, INCOMPLETE, IN_PROGRESS)

        Returns:
            Annotated queryset with update status fields
        """
        # Import Owner model to access UpdateStatus enum
        owner_model = self.model

        sections = self.update_section_class.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    self.update_status_relation,
                    filter=Q(
                        **{f"{self.update_status_relation}__section__in": sections}
                    ),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    self.update_status_relation,
                    filter=Q(
                        **{
                            f"{self.update_status_relation}__section__in": sections,
                            f"{self.update_status_relation}__is_success": True,
                        }
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    self.update_status_relation,
                    filter=Q(
                        **{
                            f"{self.update_status_relation}__section__in": sections,
                            f"{self.update_status_relation}__is_success": False,
                        }
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    self.update_status_relation,
                    filter=Q(
                        **{
                            f"{self.update_status_relation}__section__in": sections,
                            f"{self.update_status_relation}__has_token_error": True,
                        }
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=models.Case(
                    models.When(
                        active=False,
                        then=models.Value(owner_model.UpdateStatus.DISABLED),
                    ),
                    models.When(
                        num_sections_token_error=1,
                        then=models.Value(owner_model.UpdateStatus.TOKEN_ERROR),
                    ),
                    models.When(
                        num_sections_failed__gt=0,
                        then=models.Value(owner_model.UpdateStatus.ERROR),
                    ),
                    models.When(
                        num_sections_ok=num_sections_total,
                        then=models.Value(owner_model.UpdateStatus.OK),
                    ),
                    models.When(
                        num_sections_total__lt=num_sections_total,
                        then=models.Value(owner_model.UpdateStatus.INCOMPLETE),
                    ),
                    default=models.Value(owner_model.UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs

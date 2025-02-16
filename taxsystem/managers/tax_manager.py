# Django
from django.db import models

# AA Voices of War
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)


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


class OwnerAuditManagerBase(models.Manager):
    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


OwnerAuditManager = OwnerAuditManagerBase.from_queryset(OwnerAuditQuerySet)


class MembersQuerySet(models.QuerySet):
    pass


class MembersManagerBase(models.Manager):
    pass


MembersManager = MembersManagerBase.from_queryset(MembersQuerySet)

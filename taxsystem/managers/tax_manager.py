# Django
from django.db import models

# AA Voices of War
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class OwnerAuditQuerySet(models.QuerySet):
    def visible_to(self, user):
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


OwnerAuditManager = OwnerAuditManagerBase.from_queryset(OwnerAuditQuerySet)


class MembersQuerySet(models.QuerySet):
    pass


class MembersManagerBase(models.Manager):
    pass


MembersManager = MembersManagerBase.from_queryset(MembersQuerySet)

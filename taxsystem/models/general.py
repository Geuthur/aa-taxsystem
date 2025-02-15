"""General Model"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """General model for app permissions"""

    class Meta:
        managed = False
        permissions = (
            ("basic_access", _("Can access this app")),
            ("manage_access", _("Can access tools Tax System")),
            ("create_access", _("Can add Corporation")),
            ("manage_own_corp", _("Can manage own Corporation")),
            ("manage_corps", _("Can manage all Corporations")),
        )
        default_permissions = ()

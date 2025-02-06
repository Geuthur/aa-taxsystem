"""General Model"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """General model for app permissions"""

    class Meta:
        managed = False
        permissions = (
            ("basic_access", _("Can access this app")),
            ("manage_access", _("Can manage Tax System")),
            ("create_access", _("Can add Corporation")),
        )
        default_permissions = ()

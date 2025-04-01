# Django
from django.db import models

from allianceauth.services.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class WalletQuerySet(models.QuerySet):
    pass


class WalletManagerBase(models.Manager):
    pass


WalletManager = WalletManagerBase.from_queryset(WalletQuerySet)

# Django
import logging

from django.db import models

logger = logging.getLogger(__name__)


class WalletQuerySet(models.QuerySet):
    pass


class WalletManagerBase(models.Manager):
    pass


WalletManager = WalletManagerBase.from_queryset(WalletQuerySet)

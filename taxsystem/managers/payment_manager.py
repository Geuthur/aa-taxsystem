# Django
from django.db import models

# AA Voices of War
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class PaymentQuerySet(models.QuerySet):
    pass


class PaymentManagerBase(models.Manager):
    pass


PaymentManager = PaymentManagerBase.from_queryset(PaymentQuerySet)

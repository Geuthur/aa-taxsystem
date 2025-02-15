# Django
from django.db import models

# AA Voices of War
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class PaymentSystemQuerySet(models.QuerySet):
    pass


class PaymentSystemManagerBase(models.Manager):
    pass


PaymentSystemManager = PaymentSystemManagerBase.from_queryset(PaymentSystemQuerySet)


class PaymentsQuerySet(models.QuerySet):
    pass


class PaymentsManagerBase(models.Manager):
    pass


PaymentsManager = PaymentsManagerBase.from_queryset(PaymentsQuerySet)

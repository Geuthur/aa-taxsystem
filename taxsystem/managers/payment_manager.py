# Django
import logging

from django.db import models

logger = logging.getLogger(__name__)


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

# Django
import logging

from django.db import models

logger = logging.getLogger(__name__)


class LogsQuerySet(models.QuerySet):
    pass


class LogsManagerBase(models.Manager):
    pass


LogsManager = LogsManagerBase.from_queryset(LogsQuerySet)

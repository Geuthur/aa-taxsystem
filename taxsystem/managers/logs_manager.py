# Django
from django.db import models

# AA Voices of War
from taxsystem.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class LogsQuerySet(models.QuerySet):
    pass


class LogsManagerBase(models.Manager):
    pass


LogsManager = LogsManagerBase.from_queryset(LogsQuerySet)

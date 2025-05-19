from django.db import models

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from taxsystem import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class LogsQuerySet(models.QuerySet):
    pass


class LogsManagerBase(models.Manager):
    pass


LogsManager = LogsManagerBase.from_queryset(LogsQuerySet)

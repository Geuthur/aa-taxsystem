# Django
from django.db import models

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class LogsQuerySet(models.QuerySet):
    pass


class LogsManagerBase(models.Manager):
    pass


LogsManager = LogsManagerBase.from_queryset(LogsQuerySet)

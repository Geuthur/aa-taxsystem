# Django
from django.db.models.signals import post_save, pre_delete

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__, models

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class HookCache:
    all_hooks = None

    def get_hooks(self):
        if self.all_hooks is None:
            hook_array = set()
            _hooks = hooks.get_hooks("taxsystem_filters")
            for app_hook in _hooks:
                for filter_model in app_hook():
                    if filter_model not in hook_array:
                        hook_array.add(filter_model)
            self.all_hooks = hook_array
        return self.all_hooks


filters = HookCache()


# pylint: disable=unused-argument
def new_filter(sender, instance, created, **kwargs):
    try:
        logger.info("New Filter %s", instance)
        if created:
            models.SmartFilter.objects.create(filter_object=instance)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("New Filter Error: %s", e)


# pylint: disable=unused-argument
def rem_filter(sender, instance, **kwargs):
    try:
        logger.info("Removing Filter %s", instance)
        models.SmartFilter.objects.get(
            object_id=instance.pk, content_type__model=instance.__class__.__name__
        ).delete()
    except models.SmartFilter.DoesNotExist:
        logger.error("Remove Filter Error: SmartFilter does not exist")
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Remove Filter Error: %s", e)


for _filter in filters.get_hooks():
    post_save.connect(new_filter, sender=_filter)
    pre_delete.connect(rem_filter, sender=_filter)

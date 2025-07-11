"""App Configuration"""

# Django
from django.apps import AppConfig

# AA TaxSystem
from taxsystem import __version__


class TaxSystemConfig(AppConfig):
    """App Config"""

    default_auto_field = "django.db.models.AutoField"
    name = "taxsystem"
    label = "taxsystem"
    verbose_name = f"Tax System v{__version__}"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        # AA TaxSystem
        import taxsystem.signals

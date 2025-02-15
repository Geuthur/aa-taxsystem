"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Example App
from taxsystem import __version__


class TaxSystemConfig(AppConfig):
    """App Config"""

    default_auto_field = "django.db.models.AutoField"
    author = "Geuthur"
    name = "taxsystem"
    label = "taxsystem"
    verbose_name = f"Tax System v{__version__}"

    def ready(self):
        # pylint: disable=import-outside-toplevel,unused-import
        import taxsystem.signals

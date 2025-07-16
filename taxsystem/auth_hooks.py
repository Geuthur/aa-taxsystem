"""Hook into Alliance Auth"""

# Standard Library
import logging

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

# AA TaxSystem
from taxsystem.models.filters import FilterAmount, FilterReason
from taxsystem.models.tax import PaymentSystem

from . import app_settings, urls

logger = logging.getLogger(__name__)


class TaxSystemMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        super().__init__(
            f"{app_settings.TAXSYSTEM_APP_NAME}",
            "fas fa-landmark fa-fw",
            "taxsystem:index",
            navactive=["taxsystem:"],
        )

    def render(self, request):
        if request.user.has_perm("taxsystem.basic_access"):
            try:
                payment_user = PaymentSystem.objects.get(user=request.user)
                self.count = 1 if not payment_user.has_paid else 0
            except PaymentSystem.DoesNotExist:
                self.count = 0
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """Register the menu item"""

    return TaxSystemMenuItem()


@hooks.register("url_hook")
def register_urls():
    """Register app urls"""

    return UrlHook(urls, "taxsystem", r"^taxsystem/")


@hooks.register("taxsystem_filters")
def filters():
    return [FilterAmount, FilterReason]

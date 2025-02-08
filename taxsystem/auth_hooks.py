"""Hook into Alliance Auth"""

# Django
# Alliance Auth
from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from taxsystem.models.filters import FilterAmount, FilterReason

from . import app_settings, urls


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

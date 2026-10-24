"""Hook into Alliance Auth"""

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth import hooks
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import MenuItemHook, UrlHook, get_extension_logger

# AA TaxSystem
from taxsystem import __title__, app_settings, urls
from taxsystem.models.corporation import (
    CorporationPaymentAccount,
    CorporationPayments,
)
from taxsystem.models.general import General
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)


class TaxSystemMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        super().__init__(
            f"{app_settings.TAXSYSTEM_APP_NAME}",
            "fas fa-landmark fa-fw",
            "taxsystem:index",
            navactive=["taxsystem:"],
        )

    def render(self, request: UserProfile):
        if General.has_perm(request.user, General.Permission.BASIC_ACCESS):
            # Check if the User has any unpaid active accounts
            user_accounts = CorporationPaymentAccount.objects.filter(
                user=request.user, status=AccountStatus.ACTIVE
            )
            self.count = 1 if any(not acc.has_paid for acc in user_accounts) else 0

            if General.has_any_perm(
                request.user,
                General.Permission.MANAGE_OWN_CORP,
                General.Permission.MANAGE_CORPS,
            ):
                # Get the count of open invoices for the Managing user
                invoices = CorporationPayments.objects.get_visible_open_invoices(
                    request.user
                )
                self.count = invoices if invoices and invoices > 0 else self.count
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

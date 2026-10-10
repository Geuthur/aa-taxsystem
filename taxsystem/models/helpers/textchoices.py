# Django
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class AccountStatus(models.TextChoices):
    """Status for Tax Accounts.
    This indicates the current status of a tax account.
    """

    ACTIVE = "active", _("Active")
    INACTIVE = "inactive", _("Inactive")
    DEACTIVATED = "deactivated", _("Deactivated")
    MISSING = "missing", _("Missing")

    def html(self, text=False) -> mark_safe:
        """Return the HTML for the status."""
        if text:
            return format_html(
                f"<span class='badge bg-{self.color()}' data-bs-tooltip='aa-taxsystem' title='{self.label}'>{self.label}</span>"
            )
        return format_html(
            f"<span class='btn btn-sm btn-square bg-{self.color()}' data-bs-tooltip='aa-taxsystem' title='{self.label}'>{self.icon()}</span>"
        )

    def color(self) -> str:
        """Return bootstrap corresponding icon class."""
        status_map = {
            self.ACTIVE: "success",
            self.INACTIVE: "warning",
            self.DEACTIVATED: "danger",
            self.MISSING: "info",
        }
        return status_map.get(self, "secondary")

    def icon(self) -> str:
        """Return description for an enum object."""
        status_map = {
            self.ACTIVE: "<i class='fas fa-check'></i>",
            self.INACTIVE: "<i class='fas fa-user-slash'></i>",
            self.DEACTIVATED: "<i class='fas fa-user-clock'></i>",
            self.MISSING: "<i class='fas fa-question'></i> ",
        }
        return status_map.get(self, "")


class PaymentRequestStatus(models.TextChoices):
    APPROVED = "approved", _("Approved")
    PENDING = "pending", _("Pending")
    REJECTED = "rejected", _("Rejected")
    NEEDS_APPROVAL = "needs_approval", _("Requires Auditor")

    def color(self) -> str:
        """Return bootstrap corresponding icon class."""
        status_map = {
            self.APPROVED: "success",
            self.PENDING: "warning",
            self.REJECTED: "danger",
            self.NEEDS_APPROVAL: "info",
        }
        return status_map.get(self, "secondary")

    def alert(self) -> str:
        """Return bootstrap corresponding badge class."""
        status_map = {
            self.APPROVED: "alert alert-success",
            self.PENDING: "alert alert-warning",
            self.REJECTED: "alert alert-danger",
            self.NEEDS_APPROVAL: "alert alert-info",
        }
        alert_html = f"<div class='text-center alert {status_map.get(self, 'alert alert-secondary')}'>{self.label}</div>"
        return alert_html


class PaymentActions(models.TextChoices):
    DEFAULT = "", ""
    STATUS_CHANGE = "Status Changed", _("Status Changed")
    PAYMENT_ADDED = "Payment Added", _("Payment Added")
    CUSTOM_PAYMENT = "Custom Payment Added", _("Custom Payment Added")
    REVISER_COMMENT = "Reviser Comment", _("Reviser Comment")


class ActionType(models.TextChoices):
    DEFAULT = "", ""
    TAX_ACCOUNT = "account", _("Tax Account")
    CORPORATION = "corporation", _("Corporation")
    FILTER = "filter", _("Filter")
    FILTER_SET = "filter_set", _("Filter Set")
    PAYMENT = "payment", _("Payment")
    SETTINGS = "settings", _("Settings")
    GROUP = "group", _("Group")


class PaymentStatus(models.TextChoices):
    """Status for Payments.
    This indicates whether a payment has been made or not.
    """

    PAID = "paid", _("Paid")
    UNPAID = "unpaid", _("Unpaid")

    def color(self) -> str:
        """Return bootstrap corresponding icon class."""
        paid_map = {
            self.PAID: "success",
            self.UNPAID: "danger",
        }
        return paid_map.get(self, "secondary")


class PaymentSystemText(models.TextChoices):
    """
    Text choices for system changes in payment history.
    """

    DEFAULT = "", ""
    ADDED = "Payment added to system", _("Payment added to system")
    AUTOMATIC = "Automated approved Payment", _("Automated approved Payment")
    REVISER = "Payment must be approved by an reviser", _(
        "Payment must be approved by an reviser"
    )


class AdminActions(models.TextChoices):
    DEFAULT = "", ""
    ADD = "Added", _("Added")
    CHANGE = "Changed", _("Changed")
    DELETE = "Deleted", _("Deleted")


class FilterMatchType(models.TextChoices):
    EXACT = "exact", _("Exact Match")
    CONTAINS = "contains", _("Contains")

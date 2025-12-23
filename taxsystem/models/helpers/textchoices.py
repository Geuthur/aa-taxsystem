# Django
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class UpdateSection(models.TextChoices):
    """
    Base Class for Update Sections.
    """

    @classmethod
    def get_sections(cls) -> list[str]:
        """Return list of section values."""
        return [choice.value for choice in cls]

    @property
    def method_name(self) -> str:
        """Return method name for this section."""
        return f"update_{self.value}"


class UpdateStatus(models.TextChoices):
    """Status for ESI data updates.
    Used to indicate the overall status of an Owner.
    """

    DISABLED = "disabled", _("disabled")
    TOKEN_ERROR = "token_error", _("token error")
    ERROR = "error", _("error")
    OK = "ok", _("ok")
    INCOMPLETE = "incomplete", _("incomplete")
    IN_PROGRESS = "in_progress", _("in progress")

    def bootstrap_icon(self) -> str:
        """Return bootstrap corresponding icon class."""
        update_map = {
            status: mark_safe(
                f"<span class='{self.bootstrap_text_style_class()}' data-bs-tooltip='aa-taxsystem' title='{self.description()}'>⬤</span>"
            )
            for status in [
                self.DISABLED,
                self.TOKEN_ERROR,
                self.ERROR,
                self.INCOMPLETE,
                self.IN_PROGRESS,
                self.OK,
            ]
        }
        return update_map.get(self, "")

    def bootstrap_text_style_class(self) -> str:
        """Return bootstrap corresponding bootstrap text style class."""
        update_map = {
            self.DISABLED: "text-muted",
            self.TOKEN_ERROR: "text-warning",
            self.INCOMPLETE: "text-warning",
            self.IN_PROGRESS: "text-info",
            self.ERROR: "text-danger",
            self.OK: "text-success",
        }
        return update_map.get(self, "")

    def description(self) -> str:
        """Return description for an enum object."""
        update_map = {
            self.DISABLED: _("Update is disabled"),
            self.TOKEN_ERROR: _("One section has a token error during update"),
            self.INCOMPLETE: _("One or more sections have not been updated"),
            self.IN_PROGRESS: _("Update is in progress"),
            self.ERROR: _("An error occurred during update"),
            self.OK: _("Updates completed successfully"),
        }
        return update_map.get(self, "")


class AccountStatus(models.TextChoices):
    """Status for Tax Accounts.
    This indicates the current status of a tax account.
    """

    ACTIVE = "active", _("active")
    INACTIVE = "inactive", _("inactive")
    DEACTIVATED = "deactivated", _("deactivated")
    MISSING = "missing", _("missing")

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
    APPROVED = "approved", _("approved")
    PENDING = "pending", _("pending")
    REJECTED = "rejected", _("rejected")
    NEEDS_APPROVAL = "needs_approval", _("requires auditor")

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


class PaymentStatus(models.TextChoices):
    """Status for Payments.
    This indicates whether a payment has been made or not.
    """

    PAID = "paid", _("paid")
    UNPAID = "unpaid", _("unpaid")

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


class CorporationUpdateSection(UpdateSection):
    """Sections for corporation updates."""

    DIVISION_NAMES = "division_names", _("Wallet Division Names")
    DIVISIONS = "divisions", _("Wallet Divisions")
    WALLET = "wallet", _("Wallet Journal")
    MEMBERS = "members", _("Members")
    TAX_ACCOUNTS = "tax_accounts", _("Tax Accounts")
    PAYMENTS = "payments", _("Payments")
    DEADLINES = "deadlines", _("Deadlines")


class AllianceUpdateSection(UpdateSection):
    """Sections for alliance updates."""

    TAX_ACCOUNTS = "tax_accounts", _("Tax Accounts")
    PAYMENTS = "payments", _("Payments")
    DEADLINES = "deadlines", _("Deadlines")


class AdminActions(models.TextChoices):
    DEFAULT = "", ""
    ADD = "Added", _("added")
    CHANGE = "Changed", _("changed")
    DELETE = "Deleted", _("deleted")


class FilterMatchType(models.TextChoices):
    EXACT = "exact", _("Exact Match")
    CONTAINS = "contains", _("Contains")

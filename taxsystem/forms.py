"""Forms for the taxsystem app."""

# Django
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.models.corporation import CorporationFilter
from taxsystem.models.logs import (
    AdminHistory,
    AlliancePaymentHistory,
    CorporationPaymentHistory,
)


def get_mandatory_form_label_text(text: str) -> str:
    """Label text for mandatory form fields"""

    required_marker = "<span class='form-required-marker'>*</span>"

    return mark_safe(
        f"<span class='form-field-required'>{text} {required_marker}</span>"
    )


class AcceptCorporationPaymentForm(forms.ModelForm):
    """Form for accepting corporation payment."""

    class Meta:
        model = CorporationPaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for accepting the payment"),
        }
        labels = {
            "comment": _("Comment (optional)"),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),
        }


class AcceptAlliancePaymentForm(forms.ModelForm):
    """Form for accepting alliance payment."""

    class Meta:
        model = AlliancePaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for accepting the payment"),
        }
        labels = {
            "comment": _("Comment (optional)"),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),
        }


class RejectCorporationPaymentForm(forms.ModelForm):
    """Form for corporation payment rejecting."""

    class Meta:
        model = CorporationPaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for rejecting the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Reject Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class RejectAlliancePaymentForm(forms.ModelForm):
    """Form for alliance payment rejecting."""

    class Meta:
        model = AlliancePaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for rejecting the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Reject Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class UndoCorporationPaymentForm(forms.ModelForm):
    """Form for corporation payment undoing."""

    class Meta:
        model = CorporationPaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for undoing the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Undo Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class UndoAlliancePaymentForm(forms.ModelForm):
    """Form for alliance payment undoing."""

    class Meta:
        model = AlliancePaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for undoing the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Undo Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class DeleteCorporationPaymentForm(forms.ModelForm):
    """Form for corporation payment deleting."""

    class Meta:
        model = CorporationPaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for deleting the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Delete Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class DeleteAlliancePaymentForm(forms.ModelForm):
    """Form for alliance payment deleting."""

    class Meta:
        model = AlliancePaymentHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for deleting the payment"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Delete Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class PaymentAddForm(forms.Form):
    """Form for payment adding."""

    amount = forms.IntegerField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Amount")),
        help_text=_("Amount to be added"),
        widget=forms.NumberInput(attrs={"min": "0"}),
    )

    comment = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Add Reason")),
        help_text=_("Reason for adding this payment"),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class DeleteMemberForm(forms.ModelForm):
    """Form for member deleting."""

    class Meta:
        model = AdminHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for deleting the member"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Delete Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class FilterDeleteForm(forms.ModelForm):
    """Form for deleting Filter."""

    class Meta:
        model = AdminHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for deleting the filter"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Delete Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class FilterSetDeleteForm(forms.ModelForm):
    """Form for deleting Filter Set."""

    class Meta:
        model = AdminHistory
        fields = ["comment"]
        help_texts = {
            "comment": _("Reason for deleting the filter set"),
        }
        labels = {
            "comment": get_mandatory_form_label_text(text=_("Delete Reason")),
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "required": "required",
                }
            ),
        }


class AddJournalFilterForm(forms.Form):
    filter_set = forms.ModelChoiceField(
        queryset=None,
        label=_("Filter Set"),
        required=True,
    )
    filter_type = forms.ChoiceField(
        choices=CorporationFilter.FilterType.choices,
        label=_("Filter Type"),
        required=True,
    )
    value = forms.CharField(
        label=_("Filter Value"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter filter value")}),
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if queryset is not None:
            self.fields["filter_set"].queryset = queryset


class CreateFilterSetForm(forms.Form):
    name = forms.CharField(
        label=_("Filter Set Name"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Enter filter set name")}),
    )
    description = forms.CharField(
        label=_("Filter Set Description"),
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": _("Enter filter set description"), "rows": 3}
        ),
    )

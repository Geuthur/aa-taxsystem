"""Forms for the taxsystem app."""

# Django
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.models.corporation import CorporationFilter, CorporationFilterSet


def get_mandatory_form_label_text(text: str) -> str:
    """Label text for mandatory form fields"""

    required_marker = "<span class='form-required-marker'>*</span>"

    return mark_safe(
        f"<span class='form-field-required'>{text} {required_marker}</span>"
    )


class PaymentRejectForm(forms.Form):
    """Form for payment rejecting."""

    reject_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for rejecting")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class PaymentDeleteForm(forms.Form):
    """Form for payment deleting."""

    delete_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for deleting payment")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class PaymentAddForm(forms.Form):
    """Form for payment adding."""

    amount = forms.IntegerField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Amount")),
        widget=forms.NumberInput(attrs={"min": "0"}),
    )

    add_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for adding payment")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class PaymentAcceptForm(forms.Form):
    """Form for payment accepting."""

    accept_info = forms.CharField(
        required=False,
        label=_("Comment") + " (optional)",
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class PaymentUndoForm(forms.Form):
    """Form for payment undoing."""

    undo_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for undoing")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class MemberDeleteForm(forms.Form):
    """Form for member deleting."""

    delete_reason = forms.CharField(
        required=False,
        label=_("Comment") + " (optional)",
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class FilterDeleteForm(forms.Form):
    """Form for deleting."""

    delete_reason = forms.CharField(
        required=False,
        label=_("Comment") + " (optional)",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    filter = forms.HiddenInput()


class TaxSwitchUserForm(forms.Form):
    """Form for switching user."""

    user = forms.HiddenInput()


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


class EditFilterSetForm(forms.ModelForm):
    class Meta:
        model = CorporationFilterSet
        fields = ["name", "description"]

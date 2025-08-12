"""Forms for the taxsystem app."""

# Django
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# AA TaxSystem
from taxsystem.models.filters import JournalFilter, JournalFilterSet


def get_mandatory_form_label_text(text: str) -> str:
    """Label text for mandatory form fields"""

    required_marker = "<span class='form-required-marker'>*</span>"

    return mark_safe(
        f"<span class='form-field-required'>{text} {required_marker}</span>"
    )


class TaxRejectForm(forms.Form):
    """Form for rejecting."""

    reject_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for rejecting")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class TaxAcceptForm(forms.Form):
    """Form for accepting."""

    accept_info = forms.CharField(
        required=False,
        label=_("Comment") + " (optional)",
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class TaxUndoForm(forms.Form):
    """Form for undoing."""

    undo_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for undoing")),
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class TaxDeleteForm(forms.Form):
    """Form for deleting."""

    delete_reason = forms.CharField(
        required=False,
        label=_("Comment") + " (optional)",
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class FilterDeleteForm(forms.Form):
    """Form for deleting."""

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
        choices=JournalFilter.FilterType.choices,
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
        model = JournalFilterSet
        fields = ["name", "description"]

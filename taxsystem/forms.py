"""Forms for the taxsystem app."""

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def get_mandatory_form_label_text(text: str) -> str:
    """Label text for mandatory form fields"""

    required_marker = "<span class='form-required-marker'>*</span>"

    return mark_safe(
        f"<span class='form-field-required'>{text} {required_marker}</span>"
    )


class TaxDeclinedForm(forms.Form):
    """Form for declining."""

    decline_reason = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(text=_("Reason for declining")),
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


class TaxSwitchUserForm(forms.Form):
    """Form for switching user."""

    user = forms.HiddenInput()

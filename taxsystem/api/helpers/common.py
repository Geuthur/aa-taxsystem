"""Common API helper functions to reduce code duplication"""

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import core
from taxsystem.api.helpers.manage import manage_payments
from taxsystem.api.helpers.statistics import (
    StatisticsResponse,
    get_members_statistics,
    get_payment_system_statistics,
    get_payments_statistics,
)
from taxsystem.api.schema import (
    CharacterSchema,
    DashboardDivisionsSchema,
    DivisionSchema,
    RequestStatusSchema,
    UpdateStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.wallet import CorporationWalletJournalEntry


def create_payment_response_data(payment, request, perms):
    """
    Create common payment response data

    Args:
        payment: Payment object (CorporationPayments or AlliancePayments)
        request: HTTP request object
        perms: User permissions

    Returns:
        dict: Dictionary containing payment response data
    """
    character_portrait = lazy.get_character_portrait_url(
        payment.character_id, size=32, as_html=True
    )

    # Create the action buttons
    actions_html = manage_payments(request=request, perms=perms, payment=payment)

    # Create the request status
    response_request_status = RequestStatusSchema(
        status=payment.get_request_status_display(),
        color=payment.RequestStatus(payment.request_status).color(),
    )

    return {
        "payment_id": payment.pk,
        "character": CharacterSchema(
            character_id=payment.character_id,
            character_name=payment.account.name,
            character_portrait=character_portrait,
        ),
        "amount": payment.amount,
        "date": payment.formatted_payment_date,
        "request_status": response_request_status,
        "division_name": payment.division_name,
        "reviser": payment.reviser,
        "reason": payment.reason,
        "actions": actions_html,
    }


def create_own_payment_response_data(payment):
    """
    Create payment response data for own payments view

    Args:
        payment: Payment object (CorporationPayments or AlliancePayments)

    Returns:
        dict: Dictionary containing payment response data
    """
    # Create the character portrait
    character_portrait = lazy.get_character_portrait_url(
        payment.character_id, size=32, as_html=True
    )

    # Create the actions
    actions = core.generate_info_button(payment)

    # Create the request status
    response_request_status = RequestStatusSchema(
        status=payment.get_request_status_display(),
        color=payment.RequestStatus(payment.request_status).color(),
    )

    return {
        "payment_id": payment.pk,
        "character": CharacterSchema(
            character_id=payment.character_id,
            character_name=payment.account.name,
            character_portrait=character_portrait,
        ),
        "amount": payment.amount,
        "date": payment.formatted_payment_date,
        "request_status": response_request_status,
        "division_name": payment.division_name,
        "reviser": payment.reviser,
        "reason": payment.reason,
        "actions": actions,
    }


def create_divisions_list(divisions):
    """
    Create divisions list with total balance

    Args:
        divisions: QuerySet of CorporationWalletDivision objects

    Returns:
        tuple: (list of DivisionSchema, total_balance)
    """
    response_divisions_list = []
    total_balance = 0

    for i, division in enumerate(divisions, start=1):
        division_name = division.name if division.name else f"{i}. {_('Division')}"
        response_divisions_list.append(
            DivisionSchema(
                name=division_name,
                balance=division.balance,
            )
        )
        total_balance += division.balance

    return response_divisions_list, total_balance


def create_statistics_response(owner):
    """
    Create statistics response for dashboard

    Args:
        owner: Owner object (CorporationOwner or AllianceOwner)

    Returns:
        StatisticsResponse: Statistics response object
    """
    return StatisticsResponse(
        owner_id=owner.pk,
        owner_name=owner.name,
        payment_system=get_payment_system_statistics(owner),
        payments=get_payments_statistics(owner),
        members=get_members_statistics(owner),
    )


def calculate_activity_html(owner, corporation_id):
    """
    Calculate activity HTML for the past 30 days

    Args:
        owner: Owner object (CorporationOwner or AllianceOwner)
        corporation_id: Corporation ID for filtering

    Returns:
        str: HTML formatted activity string
    """
    past30_days = (
        CorporationWalletJournalEntry.objects.filter(
            division__corporation=(
                owner if hasattr(owner, "eve_corporation") else owner.corporation
            ),
            date__gte=timezone.now() - timezone.timedelta(days=30),
        )
        .exclude(first_party_id=corporation_id, second_party_id=corporation_id)
        .aggregate(total=Sum("amount"))
    )

    total_amount = past30_days.get("total", 0) or 0
    activity_color = "text-success" if total_amount >= 0 else "text-danger"
    return f"<span class='{activity_color}'>{intcomma(total_amount, use_l10n=True)}</span> ISK"


def create_dashboard_common_data(owner, divisions):
    """
    Create common dashboard data structure

    Args:
        owner: Owner object (CorporationOwner or AllianceOwner)
        divisions: QuerySet of CorporationWalletDivision objects

    Returns:
        dict: Dictionary containing common dashboard data
    """
    # Create divisions
    response_divisions_list, total_balance = create_divisions_list(divisions)

    # Create statistics
    response_statistics = create_statistics_response(owner)

    return {
        "update_status": UpdateStatusSchema(
            status=owner.get_update_status,
            icon=owner.get_status.bootstrap_icon(),
        ),
        "tax_amount": owner.tax_amount,
        "tax_period": owner.tax_period,
        "divisions": DashboardDivisionsSchema(
            divisions=response_divisions_list,
            total_balance=total_balance,
        ),
        "statistics": response_statistics,
    }


def create_member_response_data(member):
    """
    Create member response data

    Args:
        member: Member object

    Returns:
        dict: Dictionary containing member response data
    """
    return {
        "character": CharacterSchema(
            character_id=member.character_id,
            character_name=member.character_name,
            character_portrait=lazy.get_character_portrait_url(
                member.character_id, size=32, as_html=True
            ),
        ),
        "is_faulty": member.is_faulty,
        "status": member.get_status_display(),
        "joined": member.joined,
    }

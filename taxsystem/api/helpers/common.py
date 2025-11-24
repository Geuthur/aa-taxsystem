"""Common API helper functions to reduce code duplication"""

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext as _

# AA TaxSystem
from taxsystem.api.helpers import core
from taxsystem.api.helpers.manage import (
    generate_filter_delete_button,
    generate_ps_add_payments_button,
    generate_ps_info_button,
    generate_ps_toggle_button,
    manage_payments,
)
from taxsystem.api.helpers.statistics import (
    StatisticsResponse,
    get_members_statistics,
    get_payment_system_statistics,
    get_payments_statistics,
)
from taxsystem.api.schema import (
    AccountSchema,
    CharacterSchema,
    DashboardDivisionsSchema,
    DataTableSchema,
    DivisionSchema,
    FilterSetModelSchema,
    RequestStatusSchema,
    UpdateStatusSchema,
)
from taxsystem.helpers import lazy
from taxsystem.models.wallet import CorporationWalletJournalEntry


def get_optimized_payments_queryset(payments_model, owner, owner_id_field):
    """
    Get optimized payments queryset with select_related to prevent N+1 queries.

    Args:
        payments_model: The payments model class (CorporationPayments or AlliancePayments)
        owner: Owner object (CorporationOwner or AllianceOwner)
        owner_id_field: The owner ID value (corporation_id or alliance_id)

    Returns:
        QuerySet: Optimized payments queryset
    """
    return (
        payments_model.objects.filter(
            account__owner=owner,
            owner_id=owner_id_field,
        )
        .select_related(
            "account",
            "account__user",
            "account__user__profile",
            "account__user__profile__main_character",
        )
        .order_by("-date")
    )


def get_optimized_own_payments_queryset(payments_model, owner, account, owner_id_field):
    """
    Get optimized own payments queryset with select_related to prevent N+1 queries.

    Args:
        payments_model: The payments model class (CorporationPayments or AlliancePayments)
        owner: Owner object (CorporationOwner or AllianceOwner)
        account: Payment account object
        owner_id_field: The owner ID value (corporation_id or alliance_id)

    Returns:
        QuerySet: Optimized own payments queryset
    """
    return (
        payments_model.objects.filter(
            account__owner=owner,
            account=account,
            owner_id=owner_id_field,
        )
        .select_related(
            "account",
            "account__user",
            "account__user__profile",
            "account__user__profile__main_character",
        )
        .order_by("-date")
    )


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


def calculate_activity(owner, corporation_id) -> float:
    """
    Calculate activity for the past 30 days

    Args:
        owner: Owner object (CorporationOwner or AllianceOwner)
        corporation_id: Corporation ID for filtering

    Returns:
        float: Activity amount
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
    return total_amount


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


def build_payments_response_list(payments, request, perms, payment_schema_class):
    """
    Build list of payment response objects from queryset.

    Generic function that works for both Corporation and Alliance payments.

    Args:
        payments: QuerySet of payment objects (CorporationPayments or AlliancePayments)
        request: Django request object
        perms: Permission flag
        payment_schema_class: Schema class to use for response (PaymentCorporationSchema or PaymentAllianceSchema)

    Returns:
        list: List of payment schema objects
    """
    response_payments_list = []
    for payment in payments:
        payment_data = create_payment_response_data(payment, request, perms)
        response_payment = payment_schema_class(**payment_data)
        response_payments_list.append(response_payment)
    return response_payments_list


def build_own_payments_response_list(payments, payment_schema_class):
    """
    Build list of own payment response objects from queryset.

    Generic function that works for both Corporation and Alliance own payments.

    Args:
        payments: QuerySet of payment objects (CorporationPayments or AlliancePayments)
        payment_schema_class: Schema class to use for response (PaymentCorporationSchema or PaymentAllianceSchema)

    Returns:
        list: List of payment schema objects
    """
    response_payments_list = []
    for payment in payments:
        payment_data = create_own_payment_response_data(payment)
        response_payment = payment_schema_class(**payment_data)
        response_payments_list.append(response_payment)
    return response_payments_list


def build_members_response_list(members, member_schema_class):
    """
    Build list of member response objects from queryset.

    Generic function that works for both Corporation and Alliance members.

    Args:
        members: QuerySet of Members objects
        member_schema_class: Schema class to use for response (MembersSchema)

    Returns:
        list: List of member schema objects
    """
    response_members_list = []
    for member in members:
        member_data = create_member_response_data(member)
        response_member = member_schema_class(**member_data)
        response_members_list.append(response_member)
    return response_members_list


def create_payment_account_response_data(account):
    """
    Create payment account response data for payment system.

    Args:
        account: Payment account object (CorporationPaymentAccount or AlliancePaymentAccount)

    Returns:
        dict: Dictionary containing payment account response data
    """
    character_id = account.user.profile.main_character.character_id
    character_name = account.user.profile.main_character.character_name

    # Create the action buttons
    actions = []
    actions.append(generate_ps_add_payments_button(account=account))
    actions.append(generate_ps_toggle_button(account=account))
    actions.append(generate_ps_info_button(account=account))
    actions_html = format_html(
        f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
    )

    return {
        "payment_id": account.pk,
        "account": AccountSchema(
            character_id=character_id,
            character_name=character_name,
            character_portrait=lazy.get_character_portrait_url(
                character_id, size=32, as_html=True
            ),
            alt_ids=account.get_alt_ids(),
        ),
        "status": account.get_payment_status(),
        "deposit": account.deposit,
        "has_paid": DataTableSchema(
            raw=str(account.has_paid),
            display=account.has_paid_icon(badge=True),
            sort=str(int(account.has_paid)),
            translation=_("Has Paid"),
            dropdown_text=_("Yes") if account.has_paid else _("No"),
        ),
        "last_paid": account.last_paid,
        "next_due": account.next_due,
        "is_active": account.is_active,
        "actions": actions_html,
    }


def build_payment_accounts_response_list(payment_accounts, payment_system_schema_class):
    """
    Build list of payment account response objects from queryset.

    Generic function that works for both Corporation and Alliance payment systems.

    Args:
        payment_accounts: QuerySet of payment account objects
        payment_system_schema_class: Schema class to use for response (PaymentSystemSchema)

    Returns:
        list: List of payment system schema objects
    """
    response_payment_accounts_list = []
    for account in payment_accounts:
        account_data = create_payment_account_response_data(account)
        response_payment_account = payment_system_schema_class(**account_data)
        response_payment_accounts_list.append(response_payment_account)
    return response_payment_accounts_list


def create_filter_response_data(filter_obj):
    """
    Create filter response data.

    Args:
        filter_obj: Filter object (CorporationFilter or AllianceFilter)

    Returns:
        dict: Dictionary containing filter response data
    """
    # Format value based on filter type
    if filter_obj.filter_type == filter_obj.__class__.FilterType.AMOUNT:
        value = f"{intcomma(filter_obj.value, use_l10n=True)} ISK"
    else:
        value = filter_obj.value

    # Create actions
    actions = []
    actions.append(generate_filter_delete_button(filter_obj=filter_obj))
    actions_html = format_html(
        f'<div class="d-flex justify-content-end">{format_html("".join(actions))}</div>'
    )

    return {
        "filter_set": FilterSetModelSchema(
            owner_id=filter_obj.filter_set.owner.pk,
            name=filter_obj.filter_set.name,
            description=filter_obj.filter_set.description,
            enabled=filter_obj.filter_set.enabled,
        ),
        "filter_type": filter_obj.get_filter_type_display(),
        "value": value,
        "actions": actions_html,
    }


def build_filters_response_list(filters, filter_schema_class):
    """
    Build list of filter response objects from queryset.

    Generic function that works for both Corporation and Alliance filters.

    Args:
        filters: QuerySet of filter objects
        filter_schema_class: Schema class to use for response (FilterModelSchema)

    Returns:
        list: List of filter schema objects
    """
    response_filters_list = []
    for filter_obj in filters:
        filter_data = create_filter_response_data(filter_obj)
        response_filter = filter_schema_class(**filter_data)
        response_filters_list.append(response_filter)
    return response_filters_list


def create_admin_log_response_data(log):
    """
    Create admin log response data.

    Args:
        log: Admin history object (CorporationAdminHistory or AllianceAdminHistory)

    Returns:
        dict: Dictionary containing admin log response data
    """
    return {
        "log_id": log.pk,
        "user_name": log.user.username,
        "date": timezone.localtime(log.date).strftime("%Y-%m-%d %H:%M"),
        "action": log.action,
        "comment": log.comment,
    }


def build_admin_logs_response_list(logs, admin_log_schema_class):
    """
    Build list of admin log response objects from queryset.

    Generic function that works for both Corporation and Alliance admin logs.

    Args:
        logs: QuerySet of admin history objects
        admin_log_schema_class: Schema class to use for response (AdminHistorySchema)

    Returns:
        list: List of admin history schema objects
    """
    response_logs_list = []
    for log in logs:
        log_data = create_admin_log_response_data(log)
        response_log = admin_log_schema_class(**log_data)
        response_logs_list.append(response_log)
    return response_logs_list

from ninja import NinjaAPI

from django.utils.translation import gettext_lazy as _

from taxsystem.api.helpers import get_corporation
from taxsystem.api.taxsystem.helpers.payments import _payments_actions
from taxsystem.api.taxsystem.helpers.paymentsystem import (
    _get_has_paid_icon,
    _payment_system_actions,
)
from taxsystem.api.taxsystem.helpers.statistics import (
    _get_divisions_dict,
    _get_statistics_dict,
)
from taxsystem.helpers import lazy
from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import Members, Payments, PaymentSystem
from taxsystem.models.wallet import CorporationWalletDivision

logger = get_extension_logger(__name__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_members(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            corporation_dict = {}

            members = Members.objects.filter(corporation=corp)

            for member in members:
                corporation_dict[member.character_id] = {
                    "character_id": member.character_id,
                    "character_portrait": lazy.get_character_portrait_url(
                        member.character_id, size=32, as_html=True
                    ),
                    "character_name": member.character_name,
                    "is_faulty": member.is_faulty,
                    "status": member.get_status_display(),
                    "joined": lazy.str_normalize_time(member.joined, hours=False),
                    "actions": "",
                }

            output = []
            output.append({"corporation": corporation_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/paymentsystem/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_paymentsystem(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            payment_system = PaymentSystem.objects.filter(
                corporation=corp
            ).select_related("user", "user__user", "user__main_character")

            payment_dict = {}

            for user in payment_system:
                actions = _payment_system_actions(corporation_id, user, perms, request)
                has_paid = _get_has_paid_icon(user)
                character_id = user.user.main_character.character_id
                payment_dict[character_id] = {
                    "character_id": character_id,
                    "character_portrait": lazy.get_character_portrait_url(
                        character_id=character_id,
                        size=32,
                        as_html=True,
                    ),
                    "character_name": user.user.main_character.character_name,
                    "alts": user.get_alt_ids(),
                    "status": user.get_payment_status(),
                    "wallet": user.payment_pool,
                    "has_paid": has_paid,
                    "has_paid_filter": has_paid["sort"],
                    "last_paid": lazy.str_normalize_time(user.last_paid, hours=True),
                    "is_active": user.is_active,
                    "actions": actions,
                }

            output = []
            output.append({"corporation": payment_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/payments/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_payments(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if corp is None:
                return 404, "Corporation Not Found"

            payments = Payments.objects.filter(payment_user__corporation=corp)

            payments_dict = {}

            for payment in payments:
                try:
                    character_id = payment.payment_user.user.main_character.character_id
                except AttributeError:
                    character_id = 0

                actions = _payments_actions(corporation_id, payment, perms, request)

                payments_dict[payment.pk] = {
                    "payment_id": payment.pk,
                    "date": payment.date,
                    "character_portrait": lazy.get_character_portrait_url(
                        character_id, size=32, as_html=True
                    ),
                    "character_name": payment.payment_user.name,
                    "amount": payment.amount,
                    "payment_date": payment.formatted_payment_date(),
                    "status": payment.get_payment_status_display(),
                    "approved": payment.get_approved_display(),
                    "system": payment.get_system_display(),
                    "reason": payment.reason,
                    "actions": actions,
                }

            output = []
            output.append({"corporation": payments_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/dashboard/",
            response={200: dict, 403: str, 404: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_dashboard(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            divisions = CorporationWalletDivision.objects.filter(corporation=corp)

            corporation_name = corp.name
            corporation_id = corp.corporation.corporation_id
            corporation_logo = lazy.get_corporation_logo_url(
                corporation_id, size=64, as_html=True
            )
            last_update_wallet = lazy.str_normalize_time(
                corp.last_update_wallet, hours=True
            )
            last_update_members = lazy.str_normalize_time(
                corp.last_update_members, hours=True
            )
            last_update_payments = lazy.str_normalize_time(
                corp.last_update_payments, hours=True
            )
            last_update_payment_system = lazy.str_normalize_time(
                corp.last_update_payment_system, hours=True
            )
            corporation_tax_amount = corp.tax_amount
            corporation_tax_period = corp.tax_period

            divisions_dict = _get_divisions_dict(divisions)
            statistics_dict = {corp.name: _get_statistics_dict(corp)}

            output = {
                "corporation_name": corporation_name,
                "corporation_id": corporation_id,
                "corporation_logo": corporation_logo,
                "last_update_wallet": last_update_wallet,
                "last_update_members": last_update_members,
                "last_update_payments": last_update_payments,
                "last_update_payment_system": last_update_payment_system,
                "tax_amount": corporation_tax_amount,
                "tax_period": corporation_tax_period,
                "divisions": divisions_dict,
                "statistics": statistics_dict,
            }

            return output

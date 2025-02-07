from ninja import NinjaAPI

from taxsystem.api.helpers import get_corporation
from taxsystem.helpers.lazy import get_character_portrait_url
from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import Members, PaymentSystem

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
                    "character_portrait": get_character_portrait_url(
                        member.character_id, size=32, as_html=True
                    ),
                    "character_name": member.character_name,
                    "is_faulty": member.is_faulty,
                    "status": member.get_status_display(),
                    "actions": "",
                }

            output = []
            output.append({"corporation": corporation_dict})

            return output

        @api.get(
            "corporation/{corporation_id}/view/payment/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_payment_users(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            payment_system = PaymentSystem.objects.filter(corporation=corp)

            payment_dict = {}

            for payment in payment_system:
                if payment.is_active:
                    payment_dict[payment.user.user.username] = {
                        "character_id": payment.user.main_character.character_id,
                        "character_portrait": get_character_portrait_url(
                            payment.user.main_character.character_id,
                            size=32,
                            as_html=True,
                        ),
                        "character_name": payment.user.main_character.character_name,
                        "alts": payment.get_alt_ids(),
                        "status": payment.get_payment_status(),
                        "actions": "",
                    }

            output = []
            output.append({"corporation": payment_dict})

            return output

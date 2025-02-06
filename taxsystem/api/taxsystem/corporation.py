from ninja import NinjaAPI

from taxsystem.api.helpers import get_corporation
from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import Members

logger = get_extension_logger(__name__)


class CorporationApiEndpoints:
    tags = ["Corporation Tax System"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/{corporation_id}/view/members/",
            response={200: list, 403: str, 404: str},
            tags=self.tags,
        )
        def get_corporation_admin(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if perms is False:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            corporation_dict = {}

            members = Members.objects.filter(audit=corp)

            for member in members:
                corporation_dict[member.character_id] = {
                    "character_id": member.character_id,
                    "character_name": member.character_name,
                    "status": member.status,
                }

            output = []
            output.append({"corporation": corporation_dict})

            return output

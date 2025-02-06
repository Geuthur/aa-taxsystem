from ninja import NinjaAPI

from taxsystem.hooks import get_extension_logger
from taxsystem.models.tax import OwnerAudit

logger = get_extension_logger(__name__)


class AdminApiEndpoints:
    tags = ["Admin"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "corporation/admin/",
            response={200: list, 403: str},
            tags=self.tags,
        )
        def get_corporation_admin(request):
            corporations = OwnerAudit.objects.visible_to(request.user)

            if corporations is None:
                return 403, "Permission Denied"

            corporation_dict = {}

            for corporation in corporations:
                # pylint: disable=broad-exception-caught
                try:
                    corporation_dict[corporation.corporation.corporation_id] = {
                        "corporation_id": corporation.corporation.corporation_id,
                        "corporation_name": corporation.corporation.corporation_name,
                    }
                except Exception:
                    continue

            output = []
            output.append({"corporation": corporation_dict})

            return output

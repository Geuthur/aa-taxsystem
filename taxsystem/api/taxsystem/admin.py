from ninja import NinjaAPI

from taxsystem.api.helpers import get_corporation
from taxsystem.helpers import lazy
from taxsystem.hooks import get_extension_logger
from taxsystem.models.logs import AdminLogs
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

        @api.get(
            "corporation/admin/{corporation_id}/view/logs/",
            response={200: list, 403: str},
            tags=self.tags,
        )
        def get_corporation_admin_logs(request, corporation_id: int):
            perms, corp = get_corporation(request, corporation_id)

            if not perms:
                return 403, "Permission Denied"

            if corp is None:
                return 404, "Corporation Not Found"

            logs = AdminLogs.objects.filter(corporation=corp).order_by("-date")

            logs_dict = {}

            for log in logs:
                date = lazy.str_normalize_time(log.date, hours=True)
                logs_dict[log.pk] = {
                    "date": date,
                    "user_name": log.user.username,
                    "action": log.action,
                    "log": log.log,
                }

            output = []
            output.append({"logs": logs_dict})

            return output

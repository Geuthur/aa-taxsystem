from taxsystem import models


def get_corporation(
    request, corporation_id
) -> tuple[bool | None, list[models.tax.OwnerAudit] | None]:
    """Get Corporation and check permissions"""
    perms = True

    try:
        corp = models.OwnerAudit.objects.get(corporation__corporation_id=corporation_id)
    except models.OwnerAudit.DoesNotExist:
        return None, None

    # Check access
    visible = models.OwnerAudit.objects.visible_to(request.user)
    if corp not in visible:
        perms = False
    return perms, corp

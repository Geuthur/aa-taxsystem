"""
Core Helpers
"""

from esi.errors import TokenError
from esi.models import Token

from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from taxsystem.providers import esi

logger = get_extension_logger(__name__)


def get_token(character_id: int, scopes: list) -> Token:
    """
    Helper method to get a valid token for a specific character with specific scopes.

    Parameters
    ----------
    character_id: `int`
    scopes: `int`

    Returns
    ----------
    `class`: esi.models.Token or False

    """
    token = (
        Token.objects.filter(character_id=character_id)
        .require_scopes(scopes)
        .require_valid()
        .first()
    )
    if token:
        return token
    return False


def get_corp_token(corp_id, scopes, req_roles):
    """
    Helper method to get a token for a specific character from a specific corp with specific scopes

    Parameters
    ----------
    corp_id: `int`
    scopes: `int`
    req_roles: `list`

    Returns
    ----------
    `class`: esi.models.Token or False

    """
    if "esi-characters.read_corporation_roles.v1" not in scopes:
        scopes.append("esi-characters.read_corporation_roles.v1")

    char_ids = EveCharacter.objects.filter(corporation_id=corp_id).values(
        "character_id"
    )
    tokens = Token.objects.filter(character_id__in=char_ids).require_scopes(scopes)

    for token in tokens:
        try:
            roles = esi.client.Character.get_characters_character_id_roles(
                character_id=token.character_id, token=token.valid_access_token()
            ).result()

            has_roles = False
            for role in roles.get("roles", []):
                if role in req_roles:
                    has_roles = True

            if has_roles:
                return token
        except TokenError as e:
            logger.error(
                "Token ID: %s (%s)",
                token.pk,
                e,
            )
    return False

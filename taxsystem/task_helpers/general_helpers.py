"""
Core Helpers
"""

from functools import wraps

# pylint: disable=no-name-in-module
from celery import signature
from celery_once import AlreadyQueued

from esi.errors import TokenError
from esi.models import Token

from allianceauth.eveonline.models import EveCharacter

from taxsystem.hooks import get_extension_logger
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


def enqueue_next_task(chain):
    """
    Queue next task, and attach the rest of the chain to it.
    """
    while len(chain):
        _t = chain.pop(0)
        _t = signature(_t)
        _t.kwargs.update({"chain": chain})
        try:
            _t.apply_async(priority=9)
        except AlreadyQueued:
            # skip this task as it is already in the queue
            logger.debug("Skipping task as its already queued %s", _t)
            continue
        break


def no_fail_chain(func):
    """
    Decorator to chain tasks provided in the chain kwargs regardless of task failures.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        excp = None
        _ret = None
        try:
            _ret = func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-exception-caught
            excp = e
        finally:
            _chn = kwargs.get("chain", [])
            enqueue_next_task(_chn)
            if excp:
                raise excp
        return _ret

    return wrapper

# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from app_utils.testing import add_character_to_user

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner, CorporationUpdateStatus


def create_corporation_owner(eve_character: EveCharacter, **kwargs) -> CorporationOwner:
    """Create a CorporationOwner from EveCharacter."""
    defaults = {
        "name": eve_character.corporation.corporation_name,
    }
    defaults.update(kwargs)
    corporation, _ = CorporationOwner.objects.get_or_create(
        eve_corporation=eve_character.corporation,
        defaults=defaults,
    )
    return corporation


def create_corporation_update_status(
    owner_audit: CorporationOwner, **kwargs
) -> CorporationUpdateStatus:
    """Create an Update Status for a CorporationOwner."""
    params = {
        "owner": owner_audit,
    }
    params.update(kwargs)
    update_status = CorporationUpdateStatus(**params)
    update_status.save()
    return update_status


def create_corporation_owner_from_user(user: User, **kwargs) -> CorporationOwner:
    """Create a CorporationOwner from a user."""
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    return create_corporation_owner(eve_character, **kwargs)


def create_user_from_evecharacter_with_access(
    character_id: int, disconnect_signals: bool = True
) -> tuple[User, CharacterOwnership]:
    """Create user with basic access from an existing EveCharacter and use it as main."""
    auth_character = EveCharacter.objects.get(character_id=character_id)
    username = StateBackend.iterate_username(auth_character.character_name)
    user = AuthUtils.create_user(username, disconnect_signals=disconnect_signals)
    user = AuthUtils.add_permission_to_user_by_name(
        "taxsystem.basic_access", user, disconnect_signals=disconnect_signals
    )
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=CorporationOwner.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )
    return user, character_ownership


def create_corporation_owner_from_evecharacter(
    character_id: int, **kwargs
) -> CorporationOwner:
    """Create a CorporationOwner from an existing EveCharacter."""

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_corporation_owner(character_ownership.character, **kwargs)


def add_auth_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True
) -> CharacterOwnership:
    auth_character = EveCharacter.objects.get(character_id=character_id)
    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=CorporationOwner.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )


def add_corporation_owner_to_user(
    user: User, character_id: int, disconnect_signals: bool = True, **kwargs
) -> CorporationOwner:
    """Add a CorporationOwner character to a user."""
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_corporation_owner(character_ownership.character, **kwargs)


def create_user_from_evecharacter_with_alliance_access(
    character_id: int, disconnect_signals: bool = True
) -> tuple[User, CharacterOwnership]:
    """Create user with basic access from an existing EveCharacter (must belong to an alliance)."""
    auth_character = EveCharacter.objects.get(character_id=character_id)
    if not auth_character.alliance_id:
        raise ValueError("Character must belong to an alliance.")

    username = StateBackend.iterate_username(auth_character.character_name)
    user = AuthUtils.create_user(username, disconnect_signals=disconnect_signals)
    user = AuthUtils.add_permission_to_user_by_name(
        "taxsystem.basic_access", user, disconnect_signals=disconnect_signals
    )
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        disconnect_signals=disconnect_signals,
    )
    return user, character_ownership

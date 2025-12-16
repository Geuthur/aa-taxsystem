# Standard Library
import datetime as dt
import random
import string

# Django
from django.contrib.auth.models import User
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Scope, Token

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AllianceFilterSet,
    AllianceOwner,
    AlliancePaymentAccount,
    AlliancePayments,
    AllianceUpdateStatus,
)
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationFilterSet,
    CorporationOwner,
    CorporationPaymentAccount,
    CorporationPayments,
    CorporationUpdateStatus,
    Members,
)
from taxsystem.models.wallet import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)


def dt_eveformat(my_dt: dt.datetime) -> str:
    """Convert datetime to EVE Online ISO format (YYYY-MM-DDTHH:MM:SS)

    Args:
        my_dt (datetime): Input datetime
    Returns:
        str: datetime in EVE Online ISO format
    """

    my_dt_2 = dt.datetime(
        my_dt.year, my_dt.month, my_dt.day, my_dt.hour, my_dt.minute, my_dt.second
    )

    return my_dt_2.isoformat()


def random_string(char_count: int) -> str:
    """returns a random string of given length"""
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(char_count)
    )


def _generate_token(
    character_id: int,
    character_name: str,
    owner_hash: str | None = None,
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    scopes: list | None = None,
    timestamp_dt: dt.datetime | None = None,
    expires_in: int = 1200,
) -> dict:
    """Generates the input to create a new SSO test token.

    Args:
        character_id (int): Character ID
        character_name (str): Character Name
        owner_hash (Optional[str], optional): Character Owner Hash. Defaults to None.
        access_token (str, optional): Access Token string. Defaults to "access_token".
        refresh_token (str, optional): Refresh Token string. Defaults to "refresh_token".
        scopes (Optional[list], optional): List of scope names. Defaults to None.
        timestamp_dt (Optional[dt.datetime], optional): Timestamp datetime. Defaults to None.
        expires_in (int, optional): Expiry time in seconds. Defaults to 1200
    Returns:
        dict: The generated token dict
    """
    if timestamp_dt is None:
        timestamp_dt = dt.datetime.utcnow()
    if scopes is None:
        scopes = [
            "esi-mail.read_mail.v1",
            "esi-wallet.read_character_wallet.v1",
            "esi-universe.read_structures.v1",
        ]
    if owner_hash is None:
        owner_hash = random_string(28)
    token = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "timestamp": int(timestamp_dt.timestamp()),
        "CharacterID": character_id,
        "CharacterName": character_name,
        "ExpiresOn": dt_eveformat(timestamp_dt + dt.timedelta(seconds=expires_in)),
        "Scopes": " ".join(list(scopes)),
        "TokenType": "Character",
        "CharacterOwnerHash": owner_hash,
        "IntellectualProperty": "EVE",
    }
    return token


def _store_as_Token(token: dict, user: object) -> Token:
    """Stores a generated token dict as Token object for given user

    Args:
        token (dict): Generated token dict
        user (User): Alliance Auth User
    Returns:
        Token: The created Token object
    """
    character_tokens = user.token_set.filter(character_id=token["CharacterID"])
    if character_tokens.exists():
        token["CharacterOwnerHash"] = character_tokens.first().character_owner_hash
    obj = Token.objects.create(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        user=user,
        character_id=token["CharacterID"],
        character_name=token["CharacterName"],
        token_type=token["TokenType"],
        character_owner_hash=token["CharacterOwnerHash"],
    )
    for scope_name in token["Scopes"].split(" "):
        scope, _ = Scope.objects.get_or_create(name=scope_name)
        obj.scopes.add(scope)
    return obj


def add_new_token(
    user: User,
    character: EveCharacter,
    scopes: list[str] | None = None,
    owner_hash: str | None = None,
) -> Token:
    """Generate a new token for a user based on a character and makes the given user it's owner.

    Args:
        user: Alliance Auth User
        character: EveCharacter to create the token for
        scopes: list of scope names
        owner_hash: optional owner hash to use for the token
    Returns:
        Token: The created Token object
    """
    return _store_as_Token(
        _generate_token(
            character_id=character.character_id,
            character_name=character.character_name,
            owner_hash=owner_hash,
            scopes=scopes,
        ),
        user,
    )


def add_character_to_user(
    user: User,
    character: EveCharacter,
    is_main: bool = False,
    scopes: list[str] | None = None,
    disconnect_signals: bool = False,
) -> CharacterOwnership:
    """Add an existing :class:`EveCharacter` to a User, optionally as main character.

    Args:
        user (User): The User to whom the EveCharacter will be added.
        character (EveCharacter): The EveCharacter to add to the User.
        is_main (bool, optional): Whether to set the EveCharacter as the User's main
            character. Defaults to ``False``.
        scopes (list[str] | None, optional): List of scope names to assign to the
            character's token. If ``None``, defaults to `["publicData"]`. Defaults to ``None``.
        disconnect_signals (bool, optional): Whether to disconnect signals during
            the addition. Defaults to ``False``.
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """

    if not scopes:
        scopes = ["publicData"]

    if disconnect_signals:
        AuthUtils.disconnect_signals()

    add_new_token(user, character, scopes)

    if is_main:
        user.profile.main_character = character
        user.profile.save()
        user.save()

    if disconnect_signals:
        AuthUtils.connect_signals()

    return CharacterOwnership.objects.get(user=user, character=character)


def create_user_from_evecharacter(
    character_id: int,
    permissions: list[str] | None = None,
    scopes: list[str] | None = None,
) -> tuple[User, CharacterOwnership]:
    """Create new allianceauth user from EveCharacter object.

    Args:
        character_id (int): ID of eve character
        permissions (list[str] | None): list of permission names, e.g. `"my_app.my_permission"`
        scopes (list[str] | None): list of scope names
    Returns:
        tuple[User, CharacterOwnership]: Created Alliance Auth User and CharacterOwnership
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    user = AuthUtils.create_user(auth_character.character_name.replace(" ", "_"))
    character_ownership = add_character_to_user(
        user, auth_character, is_main=True, scopes=scopes
    )
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
    return user, character_ownership


def add_permission_to_user(
    user: User,
    permissions: list[str] | None = None,
) -> User:
    """Add permission to existing allianceauth user.
    Args:
        user (User): Alliance Auth User
        permissions (list[str] | None): list of permission names, e.g. `"my_app.my_permission"`
    Returns:
        User: Updated Alliance Auth User
    """
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
            return user
    raise ValueError("No permissions provided to add to user.")


def create_tax_owner(
    eve_character: EveCharacter, tax_type="Corporation", **kwargs
) -> CorporationOwner | AllianceOwner:
    """
    Create a Tax Owner (CorporationOwner or AllianceOwner) from an EveCharacter.
    The type of owner created depends on the tax_type parameter.
    Args:
        eve_character (EveCharacter): The EveCharacter to create the owner from.
        tax_type (str): Type of tax owner, either "Corporation" or "Alliance"
    Returns:
        CorporationOwner | AllianceOwner: The created tax owner.

    """
    defaults = {
        "name": eve_character.corporation.corporation_name,
    }
    defaults.update(kwargs)
    owner = CorporationOwner.objects.get_or_create(
        eve_corporation=eve_character.corporation,
        defaults=defaults,
    )[0]
    if tax_type == "Alliance":
        corporation = owner
        defaults = {
            "name": eve_character.alliance.alliance_name,
        }
        defaults.update(kwargs)
        owner = AllianceOwner.objects.get_or_create(
            eve_alliance=eve_character.alliance,
            corporation=corporation,
            defaults=defaults,
        )[0]
    return owner


def create_update_status(
    owner_audit: CorporationOwner, tax_type="Corporation", **kwargs
) -> CorporationUpdateStatus | AllianceUpdateStatus:
    """
    Create an Update Status for a CorporationOwner.
    The type of update status created depends on the tax_type parameter.
    Args:
        owner_audit (CorporationOwner): The owner for whom to create the update status.
        tax_type (str): Type of tax owner, either "Corporation" or "Alliance
    """
    params = {
        "owner": owner_audit,
    }
    params.update(kwargs)
    if tax_type == "Alliance":
        update_status = AllianceUpdateStatus(**params)
    else:
        update_status = CorporationUpdateStatus(**params)
    update_status.save()
    return update_status


def create_owner_from_user(
    user: User, tax_type="Corporation", **kwargs
) -> CorporationOwner | AllianceOwner:
    """
    Create a CorporationOwner or AllianceOwner from a user.
    The type of owner created depends on the tax_type parameter.

    Args:
        user (User): The user to create the owner from.
        tax_type (str): Type of tax owner, either "Corporation" or "Alliance
    """
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    return create_tax_owner(eve_character, tax_type=tax_type, **kwargs)


def create_owner_from_evecharacter(
    character_id: int, tax_type="Corporation", **kwargs
) -> CorporationOwner | AllianceOwner:
    """
    Create a CorporationOwner or AllianceOwner from an existing EveCharacter.
    The type of owner created depends on the tax_type parameter.

    Args:
        character_id (int): ID of the EveCharacter to create the owner from.
        tax_type (str): Type of tax owner, either "Corporation" or "Alliance
    Returns:
        CorporationOwner | AllianceOwner: The created tax owner.
    """

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_tax_owner(character_ownership.character, tax_type=tax_type, **kwargs)


def create_user_from_evecharacter_with_access(
    character_id: int, disconnect_signals: bool = True
) -> tuple[User, CharacterOwnership]:
    """
    Create user with basic access from an existing EveCharacter and use it as main.

    Args:
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during user creation. Defaults to True.
    Returns:
        tuple[User, CharacterOwnership]: Created Alliance Auth User and CharacterOwnership
    """
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


def add_auth_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True
) -> CharacterOwnership:
    """Add an existing :class:`EveCharacter` to a User.

    Args:
        user (User): Alliance Auth User
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during addition. Defaults to True.
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=CorporationOwner.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )


def add_owner_to_user(
    user: User,
    character_id: int,
    disconnect_signals: bool = True,
    tax_type="Corporation",
    **kwargs,
) -> CorporationOwner | AllianceOwner:
    """
    Add a CorporationOwner or AllianceOwner character to a user.
    The type of owner created depends on the tax_type parameter.

    Args:
        user (User): Alliance Auth User
        character_id (int): ID of eve character
        disconnect_signals (bool, optional): Whether to disconnect signals during addition. Defaults to True.
        tax_type (str): Type of tax owner, either "Corporation" or "Alliance
    Returns:
        CorporationOwner | AllianceOwner: The created tax owner.
    """
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_tax_owner(character_ownership.character, tax_type=tax_type, **kwargs)


def create_payment(
    account: CorporationPaymentAccount | AlliancePaymentAccount, **kwargs
) -> CorporationPayments | AlliancePayments:
    """Create a Payment for a Corporation or Alliance
    The type of payment created depends on the type of account provided.

    Args:
        account (CorporationPaymentAccount | AlliancePaymentAccount): The payment account.
    Returns:
        CorporationPayments | AlliancePayments: The created payment.
    """
    params = {
        "account": account,
    }
    params.update(kwargs)
    if isinstance(account, AlliancePaymentAccount):
        payment = AlliancePayments(**params)
    else:
        payment = CorporationPayments(**params)
    payment.save()
    return payment


def create_member(owner: CorporationOwner, **kwargs) -> Members:
    """
    Create a Member for a Corporation

    Args:
        owner (CorporationOwner): The owner.
    Returns:
        Members: The created member.
    """
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    member = Members(**params)
    member.save()
    return member


def create_tax_account(
    owner: CorporationOwner | AllianceOwner, **kwargs
) -> CorporationPaymentAccount | AlliancePaymentAccount:
    """
    Create a Tax Account for a Corporation or Alliance
    The type of tax account created depends on the type of owner provided.

    Args:
        owner (CorporationOwner | AllianceOwner): The owner.
    Returns:
        CorporationPaymentAccount | AlliancePaymentAccount: The created tax account.
    """
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    if isinstance(owner, AllianceOwner):
        tax_account = AlliancePaymentAccount(**params)
    else:
        tax_account = CorporationPaymentAccount(**params)
    tax_account.save()
    return tax_account


def create_division(owner: CorporationOwner, **kwargs) -> CorporationWalletDivision:
    """
    Create a CorporationWalletDivision

    Args:
        owner (CorporationOwner): The owner.
    Returns:
        CorporationWalletDivision: The created division.
    """
    params = {
        "corporation": owner,
    }
    params.update(kwargs)
    division = CorporationWalletDivision(**params)
    division.save()
    return division


def create_wallet_journal_entry(**kwargs) -> CorporationWalletJournalEntry:
    """
    Create a CorporationWalletJournalEntry

    Args:
        kwargs: Fields for the CorporationWalletJournalEntry
    Returns:
        CorporationWalletJournalEntry: The created journal entry.
    """
    params = {}
    params.update(kwargs)
    journal_entry = CorporationWalletJournalEntry(**params)
    journal_entry.save()
    return journal_entry


def create_filterset(
    owner: CorporationOwner | AllianceOwner, **kwargs
) -> CorporationFilterSet | AllianceFilterSet:
    """Create a FilterSet for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    if isinstance(owner, AllianceOwner):
        journal_filter_set = AllianceFilterSet(**params)
    else:
        journal_filter_set = CorporationFilterSet(**params)
    journal_filter_set.save()
    return journal_filter_set


def create_filter(
    filter_set: CorporationFilterSet | AllianceFilterSet, **kwargs
) -> CorporationFilter | AllianceFilter:
    """Create a Filter for a Corporation"""
    params = {
        "filter_set": filter_set,
    }
    params.update(kwargs)
    if isinstance(filter_set, AllianceFilterSet):
        journal_filter = AllianceFilter(**params)
    else:
        journal_filter = CorporationFilter(**params)
    journal_filter.save()
    return journal_filter

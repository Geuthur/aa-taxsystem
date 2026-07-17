# Standard Library
from typing import Generic, TypeVar

# Third Party
import factory
import factory.fuzzy

# Django
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils

# AA TaxSystem
from taxsystem.models import (
    AllianceFilter,
    AllianceFilterSet,
    AllianceOwner,
    AlliancePaymentAccount,
    AlliancePaymentHistory,
    AlliancePayments,
    AllianceUpdateStatus,
    CorporationFilter,
    CorporationFilterSet,
    CorporationOwner,
    CorporationPaymentAccount,
    CorporationPaymentHistory,
    CorporationPayments,
    CorporationUpdateStatus,
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
    EveEntity,
    Members,
)
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    AllianceUpdateSection,
    CorporationUpdateSection,
    PaymentActions,
    PaymentRequestStatus,
)
from taxsystem.tests.testdata.utils import add_character_to_user

T = TypeVar("T")
User = get_user_model()


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    def __call__(cls, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


class UserFactory(factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[User]):
    """Generate a User object."""

    class Meta:
        model = User
        django_get_or_create = ("username",)
        exclude = ("_generated_name",)

    _generated_name = factory.Faker("name")
    username = factory.LazyAttribute(lambda obj: obj._generated_name.replace(" ", "_"))
    first_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[0])
    last_name = factory.LazyAttribute(lambda obj: obj._generated_name.split(" ")[1])
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com"
    )

    @factory.post_generation
    def permissions(obj, create, extracted, **kwargs):
        """Set default permissions. Overwrite with `permissions=["app.perm1"]`."""
        if not create:
            return
        permissions = extracted or []
        for permission_name in permissions:
            AuthUtils.add_permission_to_user_by_name(permission_name, obj)

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        """Reset permission cache to force an update."""
        super()._after_postgeneration(obj, create, results)
        if hasattr(obj, "_perm_cache"):
            del obj._perm_cache
        if hasattr(obj, "_user_perm_cache"):
            del obj._user_perm_cache


class UserMainFactory(UserFactory):
    """Generate a User object with a main character and default permissions for TaxSystem."""

    permissions__ = ["taxsystem.basic_access"]

    @factory.post_generation
    def main_character(obj, create, _, **kwargs):
        if not create:
            return
        if "character" in kwargs:
            character = kwargs["character"]
        else:
            character_name = f"{obj.first_name} {obj.last_name}"
            character = EveCharacterFactory(character_name=character_name)

        scopes = CorporationOwner.get_esi_scopes()
        add_character_to_user(
            user=obj, character=character, is_main=True, scopes=scopes
        )


class EveAllianceInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveAllianceInfo]
):
    """Generate an EveAllianceInfo object."""

    class Meta:
        model = EveAllianceInfo
        django_get_or_create = ("alliance_id", "alliance_name")

    alliance_name = factory.Faker("catch_phrase")
    alliance_ticker = factory.LazyAttribute(lambda obj: obj.alliance_name[:4].upper())
    executor_corp_id = 0

    @factory.lazy_attribute
    def alliance_id(self):
        last_id = (
            EveAllianceInfo.objects.aggregate(Max("alliance_id"))["alliance_id__max"]
            or 99_000_000
        )
        return last_id + 1


class EveCorporationInfoFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCorporationInfo]
):
    """Generate an EveCorporationInfo object."""

    class Meta:
        model = EveCorporationInfo
        django_get_or_create = ("corporation_id", "corporation_name")

    corporation_name = factory.Faker("catch_phrase")
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation_name[:4].upper()
    )
    member_count = factory.fuzzy.FuzzyInteger(1000)

    @factory.lazy_attribute
    def corporation_id(self):
        last_id = (
            EveCorporationInfo.objects.aggregate(Max("corporation_id"))[
                "corporation_id__max"
            ]
            or 98_000_000
        )
        return last_id + 1

    @factory.post_generation
    def create_alliance(obj, create, extracted, **kwargs):
        if not create or extracted is False or obj.alliance:
            return
        obj.alliance = EveAllianceInfoFactory(executor_corp_id=obj.corporation_id)


class EveCharacterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveCharacter]
):
    """
    Generate an EveCharacter object.

    Args:
        character_name (str): The name of the EveCharacter.
        corporation (EveCorporationInfo, optional): The EveCorporationInfo object associated with the character. If not provided, it will be created.
        corporation_id (int): The ID of the corporation associated with the character.
        corporation_name (str): The name of the corporation associated with the character.
        corporation_ticker (str): The ticker of the corporation associated with the character.
        character_id (int): The unique ID for the character. If not provided, it will be generated.
        alliance_id (int): The ID of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_name (str): The name of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
        alliance_ticker (str): The ticker of the alliance associated with the character's corporation. If not provided, it will be derived from the corporation.
    """

    class Meta:
        model = EveCharacter
        django_get_or_create = ("character_id", "character_name")
        exclude = ("corporation",)

    character_name = factory.Faker("name")
    corporation = factory.SubFactory(EveCorporationInfoFactory)
    corporation_id = factory.LazyAttribute(lambda obj: obj.corporation.corporation_id)
    corporation_name = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_name
    )
    corporation_ticker = factory.LazyAttribute(
        lambda obj: obj.corporation.corporation_ticker
    )

    @factory.lazy_attribute
    def character_id(self):
        last_id = (
            EveCharacter.objects.aggregate(Max("character_id"))["character_id__max"]
            or 90_000_000
        )
        return last_id + 1

    @factory.lazy_attribute
    def alliance_id(self):
        return (
            self.corporation.alliance.alliance_id if self.corporation.alliance else None
        )

    @factory.lazy_attribute
    def alliance_name(self):
        return (
            self.corporation.alliance.alliance_name if self.corporation.alliance else ""
        )

    @factory.lazy_attribute
    def alliance_ticker(self):
        return (
            self.corporation.alliance.alliance_ticker
            if self.corporation.alliance
            else ""
        )


class EveEntityFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[EveEntity]
):
    """
    Generate an EveEntity object.

    Args:
        name (str): The name of the EveEntity.
        category (str): The category of the EveEntity, which can be "character", "corporation", or "alliance".
        id (int): The unique ID for the EveEntity. If not provided, it will be generated.
    """

    class Meta:
        model = EveEntity
        django_get_or_create = ("id", "name")

    name = factory.Faker("name")
    category = factory.fuzzy.FuzzyChoice(["character", "corporation", "alliance"])

    @factory.lazy_attribute
    def id(self):
        last_id = EveEntity.objects.aggregate(Max("id"))["id__max"] or 90_000_000
        return last_id + 1


class CorporationOwnerFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationOwner]
):
    """
    Generate a CorporationOwner object.

    Args:
        user (User, optional): The user associated with the corporation owner. If not provided, it will be created.
        eve_corporation (EveCorporationInfo): The EveCorporationInfo object associated with the corporation owner.
        name (str): The name of the corporation owner, derived from the EveCorporationInfo object.
    """

    class Meta:
        model = CorporationOwner
        exclude = ("user",)

    user = factory.SubFactory(UserMainFactory)
    eve_corporation = factory.LazyAttribute(
        lambda o: o.user.profile.main_character.corporation
    )
    name = factory.LazyAttribute(lambda o: o.eve_corporation.corporation_name)


class AllianceOwnerFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AllianceOwner]
):
    """
    Generate an AllianceOwner object.

    Args:
        user (User, optional): The user associated with the alliance owner. If not provided, it will be created.
        corporation (CorporationOwner, optional): The corporation owner associated with the alliance owner. If not provided, it will be derived from the user's main character's corporation.
        eve_alliance (EveAllianceInfo): The EveAllianceInfo object associated with the alliance owner.
        name (str): The name of the alliance owner, derived from the EveAllianceInfo object.

    """

    class Meta:
        model = AllianceOwner
        exclude = ("user",)

    user = factory.SubFactory(UserMainFactory)

    @factory.lazy_attribute
    def corporation(self):
        # Try to get the CorporationOwner for the user, if it exists
        corp = CorporationOwner.objects.filter(
            eve_corporation=self.user.profile.main_character.corporation
        ).first()
        if corp:
            return corp
        # If none exists, create a new one
        return CorporationOwnerFactory(user=self.user)

    eve_alliance = factory.LazyAttribute(
        lambda o: o.corporation.eve_corporation.alliance
    )
    name = factory.LazyAttribute(lambda o: o.eve_alliance.alliance_name)


class DivisionFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationWalletDivision],
):
    """
    Generate a CorporationWalletDivision object.

    Args:
        name (str): The name of the division.
        balance (Decimal): The balance of the division.
        corporation (CorporationOwner, optional): The corporation associated with the division. If not provided, it will be created.
        division_id (int): The unique ID for the division.
    """

    class Meta:
        model = CorporationWalletDivision
        django_get_or_create = ("division_id",)

    name = factory.Faker("name")
    balance = factory.fuzzy.FuzzyDecimal(1000, 1000000, 2)
    corporation = factory.SubFactory(CorporationOwnerFactory)

    @factory.lazy_attribute
    def division_id(self):
        last_id = (
            CorporationWalletDivision.objects.filter(
                corporation=self.corporation
            ).aggregate(Max("division_id"))["division_id__max"]
            or 0
        )
        return last_id + 1


class CorporationJournalFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationWalletJournalEntry],
):
    """Generate a CorporationWalletJournalEntry object.

    Args:
        division (CorporationWalletDivision, optional): The division associated with the journal entry. If not provided, it will be created.
        entry_id (int): The unique entry ID for the journal entry.
        amount (Decimal): The amount of the journal entry.
        balance (Decimal): The balance after the journal entry.
        context_id (int): The context ID associated with the journal entry.
        context_id_type (str): The type of the context ID.
        date (datetime): The date and time of the journal entry.
        description (str): A description of the journal entry.
        first_party (EveEntity, optional): The first party involved in the journal entry. If not provided, it will be created.
        id (int): The unique ID for the journal entry.
        reason (str): The reason for the journal entry.
        ref_type (str): The reference type of the journal entry.
        second_party (EveEntity, optional): The second party involved in the journal entry. If not provided, it will be created.
        tax (Decimal): The tax amount associated with the journal entry.
        tax_receiver_id (int): The ID of the tax receiver associated with the journal entry.
    """

    _CONTEXT_ID_TYPE_CHOICES = [
        "structure_id",
        "station_id",
        "market_transaction_id",
        "character_id",
        "corporation_id",
        "alliance_id",
        "eve_system",
        "industry_job_id",
        "contract_id",
        "planet_id",
        "system_id",
        "type_id",
    ]

    _REF_TYPE_CHOICES = [
        "bounty_prizes",
        "market_transaction",
        "industry_job",
        "contract_reward",
        "industry_job_tax",
        "planetary_tax",
        "ess_escrow_transfer",
    ]

    class Meta:
        model = CorporationWalletJournalEntry
        django_get_or_create = ("entry_id",)

    division = factory.SubFactory(DivisionFactory)
    entry_id = factory.Sequence(lambda n: n + 1)

    amount = factory.fuzzy.FuzzyDecimal(-100000, 100000, 0)
    balance = factory.LazyAttribute(lambda o: o.division.balance + o.amount)
    context_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    context_id_type = factory.fuzzy.FuzzyChoice(_CONTEXT_ID_TYPE_CHOICES)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    description = factory.Faker("sentence")
    first_party = factory.SubFactory(EveEntityFactory)
    id = factory.Sequence(lambda n: n + 1)
    reason = factory.Faker("sentence")
    ref_type = factory.fuzzy.FuzzyChoice(_REF_TYPE_CHOICES)
    second_party = factory.SubFactory(EveEntityFactory)
    tax = factory.fuzzy.FuzzyDecimal(0, 10000, 2)
    tax_receiver_id = factory.fuzzy.FuzzyInteger(1, 1000000)


class CorporationFilterSetFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationFilterSet]
):
    """Generate a CorporationFilterSet object."""

    class Meta:
        model = CorporationFilterSet
        django_get_or_create = ("name",)

    owner = factory.SubFactory(CorporationOwnerFactory)

    name = factory.Faker("catch_phrase")
    description = factory.Faker("sentence")
    enabled = factory.fuzzy.FuzzyChoice([True, False])


class AllianceFilterSetFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AllianceFilterSet]
):
    """Generate an AllianceFilterSet object."""

    class Meta:
        model = AllianceFilterSet
        django_get_or_create = ("name",)

    owner = factory.SubFactory(AllianceOwnerFactory)

    name = factory.Faker("catch_phrase")
    description = factory.Faker("sentence")
    enabled = factory.fuzzy.FuzzyChoice([True, False])


class CorporationFilterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationFilter]
):
    """Generate a CorporationFilter object."""

    class Meta:
        model = CorporationFilter
        django_get_or_create = ("filter_type", "filter_set")

    filter_set = factory.SubFactory(CorporationFilterSetFactory)

    filter_type = factory.fuzzy.FuzzyChoice(["reason", "amount"])
    match_type = factory.fuzzy.FuzzyChoice(["exact", "contains"])
    value = factory.Faker("word")


class AllianceFilterFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AllianceFilter]
):
    """Generate an AllianceFilter object."""

    class Meta:
        model = AllianceFilter
        django_get_or_create = ("filter_type", "filter_set")

    filter_set = factory.SubFactory(AllianceFilterSetFactory)

    filter_type = factory.fuzzy.FuzzyChoice(["reason", "amount"])
    match_type = factory.fuzzy.FuzzyChoice(["exact", "contains"])
    value = factory.Faker("word")


class CorporationTaxAccountFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationPaymentAccount],
):
    """Generate a CorporationPaymentAccount object for tax accounts."""

    class Meta:
        model = CorporationPaymentAccount
        django_get_or_create = ("user", "owner")

    user = factory.SubFactory(UserMainFactory)
    owner = factory.SubFactory(CorporationOwnerFactory)

    name = factory.LazyAttribute(lambda o: o.user.username)
    date = factory.LazyFunction(timezone.now)
    status = factory.fuzzy.FuzzyChoice(AccountStatus.values)
    deposit = factory.fuzzy.FuzzyDecimal(0, 1000000, 2)

    last_paid = None
    last_notification = None
    notice = None


class AllianceTaxAccountFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AlliancePaymentAccount]
):
    """Generate an AlliancePaymentAccount object for tax accounts."""

    class Meta:
        model = AlliancePaymentAccount
        django_get_or_create = ("user", "owner")

    user = factory.SubFactory(UserMainFactory)
    owner = factory.SubFactory(AllianceOwnerFactory)

    name = factory.LazyAttribute(lambda o: o.user.username)
    date = factory.LazyFunction(timezone.now)
    status = factory.fuzzy.FuzzyChoice(AccountStatus.values)
    deposit = factory.fuzzy.FuzzyDecimal(0, 1000000, 2)

    last_paid = None
    last_notification = None
    notice = None


class CorporationPaymentsFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[CorporationPayments]
):
    """Generate a CorporationPayments object for payment accounts."""

    class Meta:
        model = CorporationPayments
        django_get_or_create = ("account", "owner", "entry_id")

    account = factory.SubFactory(CorporationTaxAccountFactory)
    owner = factory.SubFactory(CorporationOwnerFactory)

    name = factory.LazyAttribute(lambda o: o.account.name)
    entry_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    journal = factory.SubFactory(CorporationJournalFactory)
    amount = factory.fuzzy.FuzzyDecimal(0, 1000000, 2)
    date = None
    reason = ""
    request_status = factory.fuzzy.FuzzyChoice(PaymentRequestStatus.values)
    reviser = ""


class AlliancePaymentsFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AlliancePayments]
):
    """Generate an AlliancePayments object for payment accounts."""

    class Meta:
        model = AlliancePayments
        django_get_or_create = ("account", "owner", "entry_id")

    account = factory.SubFactory(AllianceTaxAccountFactory)
    owner = factory.SubFactory(AllianceOwnerFactory)

    name = factory.LazyAttribute(lambda o: o.account.name)
    entry_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    journal = factory.SubFactory(CorporationJournalFactory)
    amount = factory.fuzzy.FuzzyDecimal(0, 1000000, 2)
    date = None
    reason = ""
    request_status = factory.fuzzy.FuzzyChoice(PaymentRequestStatus.values)
    reviser = ""


class MembersFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[Members]
):
    """Generate a Members object for testing."""

    _STATUS_CHOICES = ["active", "missing", "noaccount", "is_alt"]

    class Meta:
        model = Members
        django_get_or_create = ("character_id", "character_name", "owner")

    character_id = factory.fuzzy.FuzzyInteger(1, 1000000)
    character_name = factory.Faker("name")
    owner = factory.SubFactory(CorporationOwnerFactory)
    status = factory.fuzzy.FuzzyChoice(_STATUS_CHOICES)
    logon = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    logged_off = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    joined = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    notice = ""


class CorporationPaymentHistoryFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationPaymentHistory],
):
    """Generate a CorporationPaymentHistory object for testing."""

    class Meta:
        model = CorporationPaymentHistory
        django_get_or_create = ("payment", "user", "new_status", "action")

    payment = factory.SubFactory(CorporationPaymentsFactory)
    new_status = factory.fuzzy.FuzzyChoice(PaymentRequestStatus.values)
    user = factory.SubFactory(UserMainFactory)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    action = factory.fuzzy.FuzzyChoice(PaymentActions.choices)
    comment = factory.Faker("sentence")


class AlliancePaymentHistoryFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AlliancePaymentHistory]
):
    """Generate an AlliancePaymentHistory object for testing."""

    class Meta:
        model = AlliancePaymentHistory
        django_get_or_create = ("payment", "user", "new_status", "action")

    payment = factory.SubFactory(AlliancePaymentsFactory)
    new_status = factory.fuzzy.FuzzyChoice(PaymentRequestStatus.values)
    user = factory.SubFactory(UserMainFactory)
    date = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    action = factory.fuzzy.FuzzyChoice(PaymentActions.choices)
    comment = factory.Faker("sentence")


class CorporationUpdateStatusFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[CorporationUpdateStatus],
):
    """Generate a CorporationUpdateStatus object for testing."""

    class Meta:
        model = CorporationUpdateStatus
        django_get_or_create = ("owner",)

    owner = factory.SubFactory(CorporationOwnerFactory)
    section = factory.fuzzy.FuzzyChoice(CorporationUpdateSection)
    is_success = factory.fuzzy.FuzzyChoice([True, False])
    error_message = factory.Faker("sentence")
    has_token_error = factory.fuzzy.FuzzyChoice([True, False])
    last_run_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_run_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )


class AllianceUpdateStatusFactory(
    factory.django.DjangoModelFactory, metaclass=BaseMetaFactory[AllianceUpdateStatus]
):
    """Generate an AllianceUpdateStatus object for testing."""

    class Meta:
        model = AllianceUpdateStatus
        django_get_or_create = ("owner",)

    owner = factory.SubFactory(AllianceOwnerFactory)
    section = factory.fuzzy.FuzzyChoice(AllianceUpdateSection)
    is_success = factory.fuzzy.FuzzyChoice([True, False])
    error_message = factory.Faker("sentence")
    has_token_error = factory.fuzzy.FuzzyChoice([True, False])
    last_run_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_run_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )
    last_update_finished_at = factory.fuzzy.FuzzyDateTime(
        start_dt=timezone.make_aware(timezone.datetime(2020, 1, 1)),
        end_dt=timezone.make_aware(timezone.datetime(2024, 12, 31)),
    )

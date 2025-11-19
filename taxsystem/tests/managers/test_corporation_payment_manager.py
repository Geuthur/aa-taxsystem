# Standard Library
from unittest.mock import MagicMock, patch
from urllib import request

# Django
from django.test import override_settings
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase, create_user_from_evecharacter

# AA TaxSystem
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationPaymentAccount,
    CorporationPayments,
)
from taxsystem.tests.testdata.generate_filter import create_filter, create_filterset
from taxsystem.tests.testdata.generate_owneraudit import create_owneraudit_from_user
from taxsystem.tests.testdata.generate_payments import (
    create_member,
    create_payment,
    create_payment_system,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse

MODULE_PATH = "taxsystem.managers.wallet_manager"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestPaymentsManager(NoSocketsTestCase):
    """Test Payments Manager for Corporation Journal Entries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter(
            1001,
        )

        cls.audit = create_owneraudit_from_user(
            user=cls.user,
            tax_amount=1000,
            tax_period=30,
        )

        cls.payment_system = create_payment_system(
            name=cls.character_ownership.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status=CorporationPaymentAccount.Status.ACTIVE,
            deposit=0,
            last_paid=(timezone.now() - timezone.timedelta(days=30)),
        )

        cls.payments = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.payments2 = create_payment(
            name=cls.character_ownership.character.character_name,
            account=cls.payment_system,
            entry_id=2,
            amount=6000,
            date=timezone.datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            reason="Mining Stuff",
            request_status=CorporationPayments.RequestStatus.PENDING,
            reviser="",
        )

        cls.filter_set = create_filterset(
            owner=cls.audit,
            name="100m",
            description="Filter for payments over 100m",
        )

        cls.filter_amount = create_filter(
            filter_set=cls.filter_set,
            filter_type=CorporationFilter.FilterType.AMOUNT,
            value=1000,
        )

    def test_update_payments(self):
        # given

        self.audit.update_payment_system(force_refresh=False)

        self.assertSetEqual(
            set(
                self.payment_system.ts_corporation_payments.values_list(
                    "entry_id", flat=True
                )
            ),
            {1, 2},
        )
        obj = self.payment_system.ts_corporation_payments.get(entry_id=1)
        self.assertEqual(obj.amount, 1000)
        self.assertEqual(obj.request_status, CorporationPayments.RequestStatus.APPROVED)

        obj = self.payment_system.ts_corporation_payments.get(entry_id=2)
        self.assertEqual(obj.amount, 6000)
        self.assertEqual(
            obj.request_status, CorporationPayments.RequestStatus.NEEDS_APPROVAL
        )

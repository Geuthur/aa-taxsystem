# Standard Library
import json
from http import HTTPStatus

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.corporation import CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import PaymentActions, PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.utils import (
    create_division,
    create_owner_from_user,
    create_payment,
    create_payment_history,
    create_tax_account,
    create_wallet_journal_entry,
)

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestPaymentsApiEndpoints(TaxSystemTestCase):
    """Test Payments API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = create_owner_from_user(user=cls.user)

        cls.division = create_division(
            corporation=cls.audit, balance=0, division_id=1, name="Main Division"
        )

        cls.first_party = EveEntity.objects.get(id=1002)
        cls.second_party = EveEntity.objects.get(id=1001)

        cls.tax_account = create_tax_account(
            name=cls.user_character.character.character_name,
            owner=cls.audit,
            user=cls.user,
            status="active",
            deposit=0,
        )

    def test_get_payments_should_200_basic_access(self):
        """
        Test that a user with 'basic_access' can access API Endpoint 'get_payments'.

        Results:
        - Access is granted
        - Payment from owner is included in the response
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Approved Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(f"{API_URL}:get_payments", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))

    def test_get_my_payments_should_200_basic_access(self):
        """
        Test that a user with 'basic_access' can access API Endpoint 'get_my_payments'.

        Results:
        - Access is granted
        - Payment from user is included in the response
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Approved Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(f"{API_URL}:get_my_payments", kwargs={"owner_id": corporation_id})
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))

    def test_get_member_payments(self):
        """
        Test 'api:get_member_payments' endpoint.

        # Test Szenarios:
            1. Member payments are returned successfully for 'manage_own_corp' Permission.
            2. Permission Denied for users without access.
            3. Member payments are returned successfully for superuser.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Approved Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={
                "owner_id": corporation_id,
                "character_id": self.user_character.character.character_id,
            },
        )
        self.client.force_login(self.manage_own_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={
                "owner_id": corporation_id,
                "character_id": self.user_character.character.character_id,
            },
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertNotIn(str(payment.amount), str(response.json()))

        # Test Data for Superuser Access
        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={
                "owner_id": corporation_id,
                "character_id": self.user_character.character.character_id,
            },
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))

    def test_get_payment_details(self):
        """
        Test 'api:get_payment_details' endpoint.

        # Test Szenarios:
            1. Payment details are returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Approved Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )
        create_payment_history(
            payment=payment,
            user=self.user,
            new_status=PaymentRequestStatus.PENDING,
            action=PaymentActions.PAYMENT_ADDED,
        )

        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))
        self.assertIn(payment.reason, str(response.json()))
        self.assertIn(str(self.audit.name), str(response.json()))

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.user2)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertNotIn(str(payment.amount), str(response.json()))
        self.assertNotIn(payment.reason, str(response.json()))
        self.assertNotIn(str(self.audit.name), str(response.json()))

    def test_add_payment(self):
        """
        Test 'api:add_payment' endpoint.

        # Test Szenarios:
            1. Payment is added successfully.
            2. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        url = reverse(
            f"{API_URL}:add_payment",
            kwargs={"owner_id": corporation_id, "account_pk": self.tax_account.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "amount": 1000,
            "comment": "Adding payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Custom Payment Added: {reason}".format(reason=data["comment"])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:add_payment",
            kwargs={"owner_id": corporation_id, "account_pk": self.tax_account.pk},
        )
        self.client.force_login(self.user)

        data = {
            "amount": 1000,
            "comment": "Adding payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_approve_payment(self):
        """
        Test approve payment endpoint.

        # Test Szenarios:
            1. Payment is approved successfully.
            2. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Pending Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:approve_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Approving payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} approved".format(
            pid=payment.pk, amount=intcomma(payment.amount), name=payment.name
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:approve_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_undo_payment(self):
        """
        Test undo payment endpoint.

        # Test Szenarios:
            1. Rejected Payment is undone successfully (should not change deposit).
            2. Approved Payment is undone successfully (should change deposit).
            3. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        self.journal_entry2 = create_wallet_journal_entry(
            division=self.division,
            entry_id=2,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        reject_payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry2,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.REJECTED,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": reject_payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Undoing payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} undone".format(
            pid=reject_payment.pk,
            amount=intcomma(reject_payment.amount),
            name=reject_payment.name,
        )
        tax_account = CorporationPaymentAccount.objects.get(pk=self.tax_account.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)
        self.assertEqual(tax_account.deposit, 0)

        # Test Data for Approved Payment
        # Approved Payment
        payment = create_payment(
            name=self.user_character.character.character_name,
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.APPROVED,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Undoing payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} undone".format(
            pid=payment.pk,
            amount=intcomma(payment.amount),
            name=payment.name,
        )
        tax_account = CorporationPaymentAccount.objects.get(pk=self.tax_account.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)
        self.assertEqual(tax_account.deposit, -1000)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_delete_payment(self):
        """
        Test delete payment endpoint.

        # Test Szenarios:
            1. Custom Payment is deleted successfully.
            2. Permission Denied for users without manage access.
            3. ESI imported Payments cannot be deleted.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Pending Payment
        payment = create_payment(
            name="Pending Payment",
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Pending Payment
        custom_payment = create_payment(
            name="Custom Payment",
            account=self.tax_account,
            owner=self.audit,
            journal=None,
            amount=2000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:delete_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": custom_payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Deleting payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} deleted - {reason}".format(
            pid=custom_payment.pk,
            amount=intcomma(custom_payment.amount),
            name=custom_payment.name,
            reason=data["comment"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:delete_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

        # Test Data for Payments that cannot be deleted
        url = reverse(
            f"{API_URL}:delete_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Deleting payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "ESI imported payments cannot be deleted"
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.json().get("message"), result)

    def test_reject_payment(self):
        """
        Test reject payment endpoint.

        # Test Szenarios:
            1. Payment is rejected successfully.
            2. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        self.journal_entry = create_wallet_journal_entry(
            division=self.division,
            entry_id=1,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            ref_type="tax_payment",
            first_party=self.first_party,
            second_party=self.second_party,
            description="Test Description",
        )

        # Pending Payment
        payment = create_payment(
            name="Pending Payment",
            account=self.tax_account,
            owner=self.audit,
            journal=self.journal_entry,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:reject_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "comment": "Rejecting payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} rejected - {reason}".format(
            pid=payment.pk,
            amount=intcomma(payment.amount),
            name=payment.name,
            reason=data["comment"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:reject_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_bulk_actions(self):
        """
        Test bulk actions endpoint.

        # Test Szenarios:
            1. Payments are approved successfully in bulk.
            2. Payments are rejected successfully in bulk.
            3. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.character.corporation_id

        # Pending Payment 1
        payment1 = create_payment(
            name="Pending Payment 1",
            account=self.tax_account,
            owner=self.audit,
            journal=None,
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        # Pending Payment 2
        payment2 = create_payment(
            name="Pending Payment 2",
            account=self.tax_account,
            owner=self.audit,
            journal=None,
            amount=2000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            reason="Tax Payment",
            request_status=PaymentRequestStatus.PENDING,
            reviser="",
        )

        url = reverse(
            f"{API_URL}:perform_bulk_actions_payments",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.manage_own_user)

        data = {
            "pks": [payment1.pk, payment2.pk],
            "action": "approve",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result (match API: list-format pks and no trailing period)
        result = (
            "Bulk '{status}' performed for {runs} payments ({pks}) for {owner}".format(
                status=PaymentRequestStatus.APPROVED,
                runs=len(data["pks"]),
                pks=str(data["pks"]),
                owner=self.audit.name,
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Reject Action
        payment1.request_status = PaymentRequestStatus.PENDING
        payment1.save()
        payment2.request_status = PaymentRequestStatus.PENDING
        payment2.save()

        url = reverse(
            f"{API_URL}:perform_bulk_actions_payments",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.manage_own_user)
        data = {
            "pks": [payment1.pk, payment2.pk],
            "action": "reject",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )
        # Expected Result (match API: list-format pks and no trailing period)
        result = (
            "Bulk '{status}' performed for {runs} payments ({pks}) for {owner}".format(
                status=PaymentRequestStatus.REJECTED,
                runs=len(data["pks"]),
                pks=str(data["pks"]),
                owner=self.audit.name,
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:perform_bulk_actions_payments",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.user)
        data = {
            "pks": [payment1.pk, payment2.pk],
            "action": "approve",
        }
        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )
        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

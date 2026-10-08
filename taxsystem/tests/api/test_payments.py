# Standard Library
import json
from http import HTTPStatus

# Django
from django.contrib.humanize.templatetags.humanize import intcomma
from django.urls import reverse
from django.utils import timezone

# AA TaxSystem
from taxsystem.models.corporation import CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import PaymentActions, PaymentRequestStatus
from taxsystem.tests import TaxSystemTestCase
from taxsystem.tests.testdata.factory import (
    CorporationJournalFactory,
    CorporationOwnerFactory,
    CorporationPaymentHistoryFactory,
    CorporationPaymentsFactory,
    CorporationTaxAccountFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.api.helpers."
API_URL = "taxsystem:api"


class TestPaymentsApiEndpoints(TaxSystemTestCase):
    """Test Payments API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = CorporationOwnerFactory(user=cls.user)
        cls.account = CorporationTaxAccountFactory(
            owner=cls.audit,
            user=cls.user,
        )

    def test_get_payments_should_200_basic_access(self):
        """
        Test that a user with 'basic_access' can access API Endpoint 'get_payments'.

        Results:
        - Access is granted
        - Payment from owner is included in the response
        """
        # Test Data
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        # Approved Payment
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        # Pending Payment
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        # Pending Payment
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )

        url = reverse(
            f"{API_URL}:get_member_payments",
            kwargs={
                "owner_id": corporation_id,
                "character_id": self.user_character.character_id,
            },
        )
        self.client.force_login(self.superuser)

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
                "character_id": self.user_character.character_id,
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
                "character_id": self.user_character.character_id,
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
        corporation_id = self.user_character.corporation_id
        user = UserMainFactory()

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        # Pending Payment
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        CorporationPaymentHistoryFactory(
            payment=payment,
            user=self.user,
            new_status=PaymentRequestStatus.PENDING,
            action=PaymentActions.PAYMENT_ADDED,
        )

        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response.json()))
        self.assertIn(payment.reason, str(response.json()))
        self.assertIn(self.audit.name, str(response.json()))

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:get_payment_details",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_add_payment(self):
        """
        Test 'api:add_payment' endpoint.

        # Test Szenarios:
            1. Payment is added successfully.
            2. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.corporation_id

        CorporationJournalFactory(
            amount=1000,
        )

        tax_account = CorporationTaxAccountFactory(
            owner=self.audit,
        )

        url = reverse(
            f"{API_URL}:add_payment",
            kwargs={"owner_id": corporation_id, "account_pk": tax_account.pk},
        )
        self.client.force_login(self.superuser)

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
            kwargs={"owner_id": corporation_id, "account_pk": tax_account.pk},
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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        # Pending Payment
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )

        url = reverse(
            f"{API_URL}:approve_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
        )

        journal_entry2 = CorporationJournalFactory(
            division=journal_entry.division,
            amount=1000,
        )

        reject_payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry2,
            amount=journal_entry2.amount,
            date=journal_entry2.date,
            request_status=PaymentRequestStatus.REJECTED,
        )

        tax_account = CorporationTaxAccountFactory(
            owner=self.audit,
            deposit=0,
        )

        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": reject_payment.pk},
        )
        self.client.force_login(self.superuser)

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
        account = CorporationPaymentAccount.objects.get(pk=tax_account.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)
        self.assertEqual(account.deposit, 0)

        # Test Data for Approved Payment
        approved_payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            account=tax_account,
            owner=self.audit,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.APPROVED,
        )

        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": approved_payment.pk},
        )
        self.client.force_login(self.superuser)

        data = {
            "comment": "Undoing payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} undone".format(
            pid=approved_payment.pk,
            amount=intcomma(approved_payment.amount),
            name=approved_payment.name,
        )
        account = CorporationPaymentAccount.objects.get(pk=tax_account.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)
        self.assertEqual(account.deposit, -1000)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": approved_payment.pk},
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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
        )

        pending_payment = CorporationPaymentsFactory(
            name="Pending Payment",
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )

        # Pending Payment
        custom_payment = CorporationPaymentsFactory(
            name="Custom Payment",
            account=pending_payment.account,
            owner=self.audit,
            journal=None,
            amount=2000,
            request_status=PaymentRequestStatus.PENDING,
        )

        url = reverse(
            f"{API_URL}:delete_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": custom_payment.pk},
        )
        self.client.force_login(self.superuser)

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
            kwargs={"owner_id": corporation_id, "payment_pk": pending_payment.pk},
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
            kwargs={"owner_id": corporation_id, "payment_pk": pending_payment.pk},
        )
        self.client.force_login(self.superuser)

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
        corporation_id = self.user_character.corporation_id

        journal_entry = CorporationJournalFactory(
            amount=1000,
            date=timezone.datetime(2025, 1, 1, 12, 0, 0),
        )

        pending_payment = CorporationPaymentsFactory(
            name="Pending Payment",
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )

        url = reverse(
            f"{API_URL}:reject_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": pending_payment.pk},
        )
        self.client.force_login(self.superuser)

        data = {
            "comment": "Rejecting payment via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Payment ID: {pid} - Amount: {amount} - Name: {name} rejected - {reason}".format(
            pid=pending_payment.pk,
            amount=intcomma(pending_payment.amount),
            name=pending_payment.name,
            reason=data["comment"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Data for Permission Denied
        url = reverse(
            f"{API_URL}:reject_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": pending_payment.pk},
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

    def test_approve_payment_should_succeed_with_empty_body(self):
        """Test approving payment without a request body succeeds."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_entry = CorporationJournalFactory(amount=1000)
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:approve_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(path=url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        payment.refresh_from_db()
        self.assertEqual(payment.request_status, PaymentRequestStatus.APPROVED)

    def test_undo_payment_should_succeed_with_empty_body(self):
        """Test undoing payment without a request body succeeds."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_entry = CorporationJournalFactory(amount=1000)
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.APPROVED,
        )
        url = reverse(
            f"{API_URL}:undo_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(path=url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        payment.refresh_from_db()
        self.assertEqual(payment.request_status, PaymentRequestStatus.PENDING)

    def test_reject_payment_should_succeed_with_empty_body(self):
        """Test rejecting payment without a request body succeeds."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_entry = CorporationJournalFactory(amount=1000)
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:reject_payment",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(path=url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        payment.refresh_from_db()
        self.assertEqual(payment.request_status, PaymentRequestStatus.REJECTED)

    def test_manage_payment_action_should_approve(self):
        """Test unified manage_payment_action endpoint approves pending payment."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_entry = CorporationJournalFactory(amount=1000)
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:manage_payment_action",
            kwargs={"owner_id": corporation_id, "payment_pk": payment.pk},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            path=url,
            data=json.dumps({"action": "approve", "comment": "Approved via action"}),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json().get("success"))
        payment.refresh_from_db()
        self.assertEqual(payment.request_status, PaymentRequestStatus.APPROVED)

    def test_get_payments_should_filter_by_scope_and_character(self):
        """Test unified get_payments endpoint with scope and character_id query parameters."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_entry = CorporationJournalFactory(amount=1500)
        payment = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_entry,
            amount=journal_entry.amount,
            date=journal_entry.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:get_payments",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.user)

        # Test Action - scope=mine
        response_mine = self.client.get(f"{url}?scope=mine")

        # Expected Result
        self.assertEqual(response_mine.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response_mine.json()))

        # Test Action - character_id filter
        self.client.force_login(self.superuser)
        response_char = self.client.get(
            f"{url}?character_id={self.user_character.character_id}"
        )

        # Expected Result
        self.assertEqual(response_char.status_code, HTTPStatus.OK)
        self.assertIn(str(payment.amount), str(response_char.json()))

    def test_bulk_payment_action_should_approve_multiple_payments(self):
        """Test bulk approve action on multiple pending payments."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_1 = CorporationJournalFactory(amount=2000)
        journal_2 = CorporationJournalFactory(amount=3000)
        payment_1 = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_1,
            amount=journal_1.amount,
            date=journal_1.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        payment_2 = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_2,
            amount=journal_2.amount,
            date=journal_2.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:manage_bulk_payment_action",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    "payment_ids": [payment_1.pk, payment_2.pk],
                    "action": "approve",
                    "comment": "Bulk approved",
                }
            ),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("processed_count"), 2)
        self.assertEqual(data.get("total_count"), 2)
        payment_1.refresh_from_db()
        payment_2.refresh_from_db()
        self.assertEqual(payment_1.request_status, PaymentRequestStatus.APPROVED)
        self.assertEqual(payment_2.request_status, PaymentRequestStatus.APPROVED)

    def test_bulk_payment_action_should_reject_multiple_payments(self):
        """Test bulk reject action on multiple pending payments."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        journal_1 = CorporationJournalFactory(amount=1000)
        payment_1 = CorporationPaymentsFactory(
            name=self.user_character.character_name,
            owner=self.audit,
            account=self.account,
            journal=journal_1,
            amount=journal_1.amount,
            date=journal_1.date,
            request_status=PaymentRequestStatus.PENDING,
        )
        url = reverse(
            f"{API_URL}:manage_bulk_payment_action",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    "payment_ids": [payment_1.pk],
                    "action": "reject",
                    "comment": "Bulk rejected for testing",
                }
            ),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("processed_count"), 1)
        payment_1.refresh_from_db()
        self.assertEqual(payment_1.request_status, PaymentRequestStatus.REJECTED)

    def test_bulk_payment_action_should_fail_when_no_ids(self):
        """Test bulk payment action fails with 400 if payment_ids is empty."""
        # Test Data
        corporation_id = self.user_character.corporation_id
        url = reverse(
            f"{API_URL}:manage_bulk_payment_action",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    "payment_ids": [],
                    "action": "approve",
                }
            ),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(response.json().get("success"))

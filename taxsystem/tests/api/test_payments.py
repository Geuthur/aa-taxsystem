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

        print(
            f"Payment created: {payment}, Amount: {payment.amount}, Owner: {payment.owner}, Date: {payment.date}, Status: {payment.request_status}"
        )
        print(
            f"User: {self.user}, Character: {self.user_character}({self.user_character.character_id}), Corporation ID: {corporation_id}"
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
        self.assertIn(str(self.audit.name), str(response.json()))

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

    def test_bulk_actions(self):
        """
        Test bulk actions endpoint.

        # Test Szenarios:
            1. Payments are approved successfully in bulk.
            2. Payments are rejected successfully in bulk.
            3. Permission Denied for users without manage access.
        """
        # Test Data
        corporation_id = self.user_character.corporation_id

        # Pending Payment 1
        payment1 = CorporationPaymentsFactory(
            name="Pending Payment 1",
            owner=self.audit,
            account=self.account,
            journal=None,
            amount=1000,
            request_status=PaymentRequestStatus.PENDING,
        )

        # Pending Payment 2
        payment2 = CorporationPaymentsFactory(
            name="Pending Payment 2",
            owner=self.audit,
            account=self.account,
            journal=None,
            amount=2000,
            request_status=PaymentRequestStatus.PENDING,
        )

        url = reverse(
            f"{API_URL}:perform_bulk_actions_payments",
            kwargs={"owner_id": corporation_id},
        )
        self.client.force_login(self.superuser)

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
        self.client.force_login(self.superuser)
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

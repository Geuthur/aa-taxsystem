# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner, CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import AccountStatus
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


class TestAdminApiEndpoints(TaxSystemTestCase):
    """Test Admin API Endpoints."""

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

    def test_get_dashboard(self):
        """
        Test 'api:get_dashboard' Endpoint.

        # Test Scenarios:
            1. Dashboard data is returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        div_names = [
            d.get("name") for d in data.get("divisions", {}).get("divisions", [])
        ]
        self.assertIn("Main Division", div_names)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_get_tax_accounts(self):
        """
        Test 'api:get_tax_accounts' Endpoint.

        # Test Scenarios:
            1. Tax Accounts are returned successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = json.loads(response.content)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["account"]["character_name"], self.tax_account.name)
        self.assertEqual(data[0]["status"], self.tax_account.get_payment_status())

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_switch_tax_account(self):
        """
        Test 'api:switch_tax_account' Endpoint.

        # Test Scenarios:
            1. Tax Account status is switched successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:switch_tax_account",
            kwargs={"owner_id": self.audit.eve_id, "account_pk": self.tax_account.pk},
        )
        self.client.force_login(self.superuser)
        data = {"new_status": "inactive", "comment": "Switching status via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        tax_account = CorporationPaymentAccount.objects.get(pk=self.tax_account.pk)
        result = "{account} switched to {status}".format(
            account=tax_account, status=tax_account.status
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:switch_tax_account",
            kwargs={"owner_id": self.audit.eve_id, "account_pk": self.tax_account.pk},
        )
        self.client.force_login(self.user)
        data = {"new_status": "active", "comment": "Switching status via API test."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_update_tax_amount(self):
        """
        Test 'api:update_tax_amount' Endpoint.

        # Test Scenarios:
            1. Tax Amount is updated successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:update_tax_amount",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.superuser)
        data = {"tax_amount": 5000}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        owner = CorporationOwner.objects.get(pk=self.audit.pk)
        result = "Tax Period from {owner} changed to {value}".format(
            owner=owner, value=float(owner.tax_amount)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:update_tax_amount",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.user)
        data = {"tax_amount": 10000}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_update_tax_period(self):
        """
        Test 'api:update_tax_period' Endpoint.

        # Test Scenarios:
            1. Tax Period is updated successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:update_tax_period",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.superuser)
        data = {"tax_period": 14}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        owner = CorporationOwner.objects.get(pk=self.audit.pk)
        result = "Tax Period from {owner} changed to {value}".format(
            owner=owner, value=owner.tax_period
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:update_tax_period",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.user)
        data = {"tax_period": 30}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

    def test_perform_bulk_actions_tax_accounts(self):
        """
        Test 'api:perform_bulk_actions_tax_accounts' Endpoint.

        # Test Scenarios:
            1. Bulk Action is performed successfully.
            2. Permission Denied for users without access.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:perform_bulk_actions_tax_accounts",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.superuser)
        data = {
            "pks": [self.tax_account.pk],
            "action": "deactivate",
            "comment": "Bulk action via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        pks_str = str(data["pks"])
        result = (
            "Bulk '{status}' performed for {items} accounts({pks}) for {owner}".format(
                status=AccountStatus.DEACTIVATED, items=1, pks=pks_str, owner=self.audit
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json().get("message"), result)

        # Test Scenario 2: Permission Denied
        url = reverse(
            f"{API_URL}:perform_bulk_actions_tax_accounts",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.user)
        data = {
            "pks": [self.tax_account.pk],
            "action": "activate",
            "comment": "Bulk action via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        result = "Permission Denied."
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json().get("error"), result)

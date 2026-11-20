# Standard Library
import json
from http import HTTPStatus

# Django
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

# Alliance Auth
from allianceauth.groupmanagement.models import Group

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner, CorporationPaymentAccount
from taxsystem.models.helpers.textchoices import AccountStatus
from taxsystem.tests import AuthTestCase
from taxsystem.tests.testdata.factory import (
    AllianceGroupFactory,
    AllianceOwnerFactory,
    AllianceTaxAccountFactory,
    CorporationGroupFactory,
    CorporationOwnerFactory,
    CorporationTaxAccountFactory,
    DivisionFactory,
    EveEntityFactory,
    UserMainFactory,
)

MODULE_PATH = "taxsystem.api.helpers."

API_URL = "taxsystem:api"


class TestAdminApiEndpoints(AuthTestCase):
    """Test Admin API Endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_character = cls.user.profile.main_character

        cls.audit = CorporationOwnerFactory(user=cls.user)

        cls.division = DivisionFactory(
            corporation=cls.audit, balance=0, division_id=1, name="Main Division"
        )

        cls.tax_account = CorporationTaxAccountFactory(
            name=cls.user_character.character_name,
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

    def _set_tax_amount(self):
        """Give the owner a tax amount, so an overdue account is unpaid."""
        CorporationOwner.objects.filter(pk=self.audit.pk).update(tax_amount=1000)

    def _create_tax_free_account(self, group_name: str, **kwargs):
        """Create an overdue account whose user is in a tax-free group of the owner."""
        self._set_tax_amount()
        user = UserMainFactory()
        group = Group.objects.create(name=group_name)
        group.user_set.add(user)
        CorporationGroupFactory(owner=self.audit, groups=[group])
        params = {
            "owner": self.audit,
            "user": user,
            "name": user.profile.main_character.character_name,
            "status": "active",
            "deposit": 0,
            "last_paid": timezone.now() - timezone.timedelta(days=400),
        }
        params.update(kwargs)
        return CorporationTaxAccountFactory(**params)

    def test_get_tax_accounts_should_mark_tax_free_group_member(self):
        # Test Data
        tax_free_account = self._create_tax_free_account("Tax Free Accounts Group")
        overdue_account = CorporationTaxAccountFactory(
            owner=self.audit,
            user=UserMainFactory(),
            status="active",
            deposit=0,
            last_paid=timezone.now() - timezone.timedelta(days=400),
        )
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = {row["account_id"]: row for row in response.json()}
        self.assertTrue(data[tax_free_account.pk]["is_tax_free"])
        self.assertIsNone(data[tax_free_account.pk]["next_due"])
        self.assertFalse(data[overdue_account.pk]["is_tax_free"])
        self.assertFalse(data[overdue_account.pk]["has_paid"])
        self.assertIsNotNone(data[overdue_account.pk]["next_due"])

    def test_get_tax_accounts_should_not_mark_deactivated_account_as_tax_free(self):
        # Test Data
        account = self._create_tax_free_account(
            "Tax Free Deactivated Group", status="deactivated"
        )
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        data = {row["account_id"]: row for row in response.json()}
        self.assertFalse(data[account.pk]["is_tax_free"])
        self.assertTrue(data[account.pk]["has_paid"])

    def test_get_tax_accounts_should_not_query_tax_free_groups_per_account(self):
        # Test Data
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)
        for number in range(1, 5):
            self._create_tax_free_account(f"Tax Free Query Group {number}")

        # Test Action
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)

        # Expected Result
        self.assertEqual(len(response.json()), 5)
        group_queries = [
            query["sql"]
            for query in queries.captured_queries
            if "corporationgroup" in query["sql"] or "auth_user_groups" in query["sql"]
        ]
        self.assertEqual(len(group_queries), 2)

    def test_get_tax_accounts_should_not_query_per_account(self):
        # Test Data
        url = reverse(
            f"{API_URL}:get_tax_accounts", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)
        self._set_tax_amount()
        CorporationTaxAccountFactory(
            owner=self.audit,
            user=UserMainFactory(),
            status="active",
            deposit=0,
            last_paid=timezone.now(),
        )
        with CaptureQueriesContext(connection) as baseline:
            self.client.get(url)
        accounts = [
            CorporationTaxAccountFactory(
                owner=self.audit,
                user=UserMainFactory(),
                status="active",
                deposit=0,
                last_paid=timezone.now(),
            )
            for _ in range(4)
        ]

        # Test Action
        with self.assertNumQueries(len(baseline.captured_queries)):
            response = self.client.get(url)

        # Expected Result
        data = {row["account_id"]: row for row in response.json()}
        self.assertEqual(len(data), 6)
        for account in accounts:
            main_id = account.user.profile.main_character.character_id
            self.assertEqual(data[account.pk]["account"]["alt_ids"], [main_id])
            self.assertTrue(data[account.pk]["has_paid"])
            self.assertIsNotNone(data[account.pk]["next_due"])

    def test_get_dashboard_should_not_count_tax_free_group_member_as_unpaid(self):
        # Test Data
        self._create_tax_free_account("Tax Free Statistics Group")
        CorporationTaxAccountFactory(
            owner=self.audit,
            user=UserMainFactory(),
            status="active",
            deposit=0,
            last_paid=timezone.now() - timezone.timedelta(days=400),
        )
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"owner_id": self.audit.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        statistics = response.json()["statistics"]["tax_account"]
        # The account from setUpClass and the overdue one, not the tax-free one
        self.assertEqual(statistics["accounts_active"], 3)
        self.assertEqual(statistics["accounts_unpaid"], 2)

    def test_get_dashboard_should_not_count_tax_free_alliance_member_as_unpaid(self):
        # Test Data
        alliance_owner = AllianceOwnerFactory(user=self.user, tax_amount=1000)
        user = UserMainFactory()
        group = Group.objects.create(name="Tax Free Alliance Statistics Group")
        group.user_set.add(user)
        AllianceGroupFactory(owner=alliance_owner, groups=[group])
        AllianceTaxAccountFactory(
            owner=alliance_owner,
            user=user,
            status="active",
            deposit=0,
            last_paid=timezone.now() - timezone.timedelta(days=400),
        )
        url = reverse(
            f"{API_URL}:get_dashboard", kwargs={"owner_id": alliance_owner.eve_id}
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        statistics = response.json()["statistics"]["tax_account"]
        self.assertEqual(statistics["accounts_active"], 1)
        self.assertEqual(statistics["accounts_unpaid"], 0)

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
        data = {
            "new_status": "deactivated",
            "comment": "Switching status via API test.",
        }

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        tax_account = CorporationPaymentAccount.objects.get(pk=self.tax_account.pk)
        result = "{account} switched to {status}".format(
            account=tax_account.name, status=tax_account.status
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

    def test_switch_tax_account_should_404_error_when_account_not_found(self):
        """Test 'api:switch_tax_account' answers 404 with an `error` body for an unknown account."""
        # Test Data
        url = reverse(
            f"{API_URL}:switch_tax_account",
            kwargs={"owner_id": self.audit.eve_id, "account_pk": 999999},
        )
        self.client.force_login(self.superuser)
        data = {"new_status": "deactivated", "comment": "Unknown account."}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.json(), {"error": "Account not found."})

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
        result = "Tax Amount from {owner} changed to {value}".format(
            owner=owner, value=owner.tax_amount
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

    def test_update_owner_settings(self):
        """
        Test 'api:update_owner_settings' Endpoint.

        # Test Scenarios:
            1. Update both tax_amount and tax_period successfully.
            2. Validation error on negative values.
            3. Permission denied.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:update_owner_settings",
            kwargs={"owner_id": self.audit.eve_id},
        )
        self.client.force_login(self.superuser)
        data = {"tax_amount": 7500, "tax_period": 21}

        # Test Action
        response = self.client.post(
            path=url, data=json.dumps(data), content_type="application/json"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        owner = CorporationOwner.objects.get(pk=self.audit.pk)
        self.assertEqual(owner.tax_amount, 7500)
        self.assertEqual(owner.tax_period, 21)

        # Negative value validation
        bad_response = self.client.post(
            path=url,
            data=json.dumps({"tax_amount": -1}),
            content_type="application/json",
        )
        self.assertEqual(bad_response.status_code, HTTPStatus.BAD_REQUEST)

        # Permission Denied
        self.client.force_login(self.user)
        denied_response = self.client.post(
            path=url,
            data=json.dumps({"tax_amount": 1000}),
            content_type="application/json",
        )
        self.assertEqual(denied_response.status_code, HTTPStatus.FORBIDDEN)

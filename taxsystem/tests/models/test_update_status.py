"""Aggregate update status of an owner (`get_status`)."""

# AA TaxSystem
from taxsystem.models.alliance import AllianceUpdateStatus
from taxsystem.models.corporation import CorporationUpdateStatus
from taxsystem.models.helpers.update_manager import (
    AllianceUpdateSection,
    CorporationUpdateSection,
    UpdateStatus,
)
from taxsystem.tests import NoSocketsTestCase
from taxsystem.tests.testdata.factory import (
    AllianceOwnerFactory,
    CorporationOwnerFactory,
)


class TestGetStatus(NoSocketsTestCase):
    """Every status value for corporation and alliance owners."""

    CASES = [
        (CorporationOwnerFactory, CorporationUpdateStatus, CorporationUpdateSection),
        (AllianceOwnerFactory, AllianceUpdateStatus, AllianceUpdateSection),
    ]

    def _check(self, expected, rows=None, active=True, missing=0):
        """
        Create an owner with one status row per section and check `get_status`.

        rows: overrides for single rows {index: {field: value}}
        missing: number of sections without a row
        """
        for owner_factory, status_model, section_class in self.CASES:
            with self.subTest(owner=status_model.__name__):
                owner = owner_factory()
                owner.active = active
                owner.save()
                sections = section_class.get_sections()
                for index, section in enumerate(sections[missing:]):
                    fields = {"is_success": True, "has_token_error": False}
                    fields.update((rows or {}).get(index, {}))
                    status_model.objects.create(owner=owner, section=section, **fields)

                self.assertEqual(owner.get_status, expected)

    def test_get_status_should_be_ok_when_all_sections_succeeded(self):
        self._check(UpdateStatus.OK)

    def test_get_status_should_be_disabled_when_owner_inactive(self):
        self._check(UpdateStatus.DISABLED, active=False)

    def test_get_status_should_be_incomplete_without_status_rows(self):
        for owner_factory, _status_model, _section_class in self.CASES:
            with self.subTest(owner=owner_factory.__name__):
                self.assertEqual(owner_factory().get_status, UpdateStatus.INCOMPLETE)

    def test_get_status_should_be_incomplete_when_a_section_is_missing(self):
        self._check(UpdateStatus.INCOMPLETE, missing=1)

    def test_get_status_should_be_error_when_a_section_failed(self):
        self._check(UpdateStatus.ERROR, rows={0: {"is_success": False}})

    def test_get_status_should_be_token_error_when_a_section_has_token_error(self):
        self._check(
            UpdateStatus.TOKEN_ERROR,
            rows={0: {"is_success": False, "has_token_error": True}},
        )

    def test_get_status_should_be_token_error_with_several_token_errors(self):
        self._check(
            UpdateStatus.TOKEN_ERROR,
            rows={
                0: {"is_success": False, "has_token_error": True},
                1: {"is_success": False, "has_token_error": True},
            },
        )

    def test_get_status_should_be_in_progress_when_a_section_is_running(self):
        self._check(UpdateStatus.IN_PROGRESS, rows={0: {"is_success": None}})


class TestUpdateStatusManager(NoSocketsTestCase):
    def test_get_status_should_return_status_of_the_filtered_owner(self):
        # Test Data
        ok_owner = CorporationOwnerFactory()
        error_owner = CorporationOwnerFactory()
        for section in CorporationUpdateSection.get_sections():
            CorporationUpdateStatus.objects.create(
                owner=ok_owner, section=section, is_success=True
            )
            CorporationUpdateStatus.objects.create(
                owner=error_owner, section=section, is_success=section != "wallet"
            )

        # Test Action / Expected Result
        self.assertEqual(
            CorporationUpdateStatus.objects.filter(owner=ok_owner).get_status(),
            UpdateStatus.OK,
        )
        self.assertEqual(
            CorporationUpdateStatus.objects.filter(owner=error_owner).get_status(),
            UpdateStatus.ERROR,
        )

    def test_get_status_should_be_incomplete_without_rows(self):
        self.assertEqual(
            AllianceUpdateStatus.objects.none().get_status(), UpdateStatus.INCOMPLETE
        )

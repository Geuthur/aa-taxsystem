# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.db.models import Case, Count, Q, Value, When
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.app_settings import TAXSYSTEM_BULK_BATCH_SIZE
from taxsystem.decorators import log_timing
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    AllianceUpdateSection,
    PaymentActions,
    PaymentRequestStatus,
    PaymentSystemText,
    UpdateStatus,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.alliance import AllianceOwner as OwnerContext
    from taxsystem.models.alliance import (
        AlliancePaymentAccount as PaymentAccountContext,
    )
    from taxsystem.models.alliance import AlliancePayments as PaymentsContext


# pylint: disable=duplicate-code
class AllianceOwnerQuerySet(models.QuerySet["OwnerContext"]):
    """QuerySet for AllianceOwner with common filtering logic."""

    def visible_to(self, user):
        """Get all allys visible to the user."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all alliances for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_alliances"):
            logger.debug("Returning all alliances for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            alliance_ids = user.character_ownerships.all().values_list(
                "character__alliance_id", flat=True
            )
            queries = [models.Q(eve_alliance__alliance_id__in=alliance_ids)]

            logger.debug(
                "%s queries for user %s visible alliances.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user):
        """Get all alliances that the user can manage."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all alliances for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_alliances"):
            logger.debug("Returning all alliances for Tax Audit Manager %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            query = None

            if user.has_perm("taxsystem.manage_own_alliance"):
                query = models.Q(eve_alliance__alliance_id=char.alliance_id)

            logger.debug("Returning own alliances for User %s.", user)

            if query is None:
                return self.none()

            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    # pylint: disable=duplicate-code
    def annotate_total_update_status(self):
        """Get the total update status."""
        sections = AllianceUpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "ts_alliance_update_status",
                    filter=Q(ts_alliance_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "ts_alliance_update_status",
                    filter=Q(
                        ts_alliance_update_status__section__in=sections,
                        ts_alliance_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class AllianceOwnerManager(models.Manager["OwnerContext"]):
    def get_queryset(self):
        return AllianceOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()


# TODO Make a all in one manager for both corp and alliance tax accounts?
class AlliancePaymentAccountManager(models.Manager["PaymentAccountContext"]):
    @log_timing(logger)
    def update_or_create_tax_accounts(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update or Create Tax Account data."""
        return owner.update_manager.update_section_if_changed(
            section=AllianceUpdateSection.PAYMENT_SYSTEM,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _update_or_create_objs(
        self, owner: "OwnerContext", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update or Create tax accounts entries from objs data."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.alliance import (
            AllianceFilterSet,
            AlliancePaymentHistory,
            AlliancePayments,
        )

        # TODO Create a Hash Tag to track changes better
        logger.debug(
            "Updating Tax Accounts for: %s",
            owner.name,
        )

        payments = AlliancePayments.objects.filter(
            account__owner=owner,
            request_status=PaymentRequestStatus.PENDING,
        )

        _current_payment_ids = set(payments.values_list("id", flat=True))
        _automatic_payment_ids = []

        # Check tax accounts before we process payments
        self._check_tax_accounts(owner)

        # Check for any automatic payments
        try:
            filters_obj = AllianceFilterSet.objects.filter(owner=owner)
            for filter_obj in filters_obj:
                # Apply filter to pending payments
                payments = filter_obj.filter(payments)
                for payment in payments:
                    if payment.request_status == PaymentRequestStatus.PENDING:
                        # Ensure all transfers are processed in a single transaction
                        with transaction.atomic():
                            payment.request_status = PaymentRequestStatus.APPROVED
                            payment.reviser = "System"

                            # Update payment pool for user
                            self.filter(owner=owner, user=payment.account.user).update(
                                deposit=payment.account.deposit + payment.amount
                            )

                            payment.save()

                            AlliancePaymentHistory(
                                user=payment.account.user,
                                payment=payment,
                                action=PaymentActions.STATUS_CHANGE,
                                new_status=PaymentRequestStatus.APPROVED,
                                comment=PaymentSystemText.AUTOMATIC,
                            ).save()

                            runs = runs + 1
                            _automatic_payment_ids.append(payment.pk)
        except AllianceFilterSet.DoesNotExist:
            pass

        # Check for any payments that need approval
        needs_approval = _current_payment_ids - set(_automatic_payment_ids)
        approvals = AlliancePayments.objects.filter(
            id__in=needs_approval,
            request_status=PaymentRequestStatus.PENDING,
        )

        for payment in approvals:
            payment.request_status = PaymentRequestStatus.NEEDS_APPROVAL
            payment.save()

            AlliancePaymentHistory(
                user=payment.account.user,
                payment=payment,
                action=PaymentActions.STATUS_CHANGE,
                new_status=PaymentRequestStatus.NEEDS_APPROVAL,
                comment=PaymentSystemText.REVISER,
            ).save()

            runs = runs + 1

        logger.debug(
            "Finished %s: Tax Accounts entrys for %s",
            runs,
            owner.name,
        )

        return ("Finished Tax Accounts for %s", owner.name)

    # pylint: disable=duplicate-code
    def _check_tax_accounts(self, owner: "OwnerContext"):
        """
        Check tax accounts for a alliance.
        Create new accounts, update existing ones, and remove orphaned accounts.
        """
        logger.debug("Checking Tax Accounts for: %s", owner.name)
        items = []

        # Get all existing accounts with a Main Character
        auth_accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__alliance_id=owner.eve_alliance.alliance_id,
        ).prefetch_related("user__profile__main_character")
        auth_accounts_ids = set(auth_accounts.values_list("user_id", flat=True))

        # If no valid accounts, return
        if not auth_accounts:
            logger.debug("No valid accounts for skipping Check: %s", owner.name)
            return "No Accounts"

        # Get existing and new accounts
        existing_accounts = self.filter(owner=owner).select_related("user")
        existing_accounts_ids = set(existing_accounts.values_list("user_id", flat=True))

        # Filter only new accounts
        new_accounts = auth_accounts.exclude(
            user__in=existing_accounts.values_list("user", flat=True)
        )

        # Cleanup orphaned accounts
        self._cleanup_orphaned_accounts(owner, auth_accounts_ids, existing_accounts_ids)

        # Update existing accounts
        for tax_account in existing_accounts:
            self._update_existing_account(tax_account)

        # Create new accounts for users without existing tax accounts
        for account in new_accounts:
            logger.debug(
                "Creating new alliance tax account for user: %s", account.user.username
            )
            items.append(
                self.model(
                    name=account.main_character.character_name,
                    owner=owner,
                    user=account.user,
                    status=AccountStatus.ACTIVE,
                )
            )

        # Bulk create new accounts
        if items:
            self.bulk_create(
                items,
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
                ignore_conflicts=True,
            )
            logger.info("Added %s new tax accounts for: %s", len(items), owner.name)
        else:
            logger.debug("No new tax accounts for: %s", owner.name)

        return ("Finished checking Tax Accounts for %s", owner.name)

    # pylint: disable=duplicate-code
    def _cleanup_orphaned_accounts(
        self, owner: "OwnerContext", auth_user_ids: set, ps_user_ids: set
    ):
        """Delete Tax accounts for users without main characters."""
        for ps_user_id in ps_user_ids:
            if ps_user_id not in auth_user_ids:
                self.filter(owner=owner, user_id=ps_user_id).delete()
                logger.info(
                    "Deleted Tax Account for user id: %s from Alliance: %s",
                    ps_user_id,
                    owner.name,
                )

    # pylint: disable=duplicate-code
    def _update_existing_account(
        self,
        tax_account: "PaymentAccountContext",
    ):
        """
        Update an existing tax account based on current state.

        Args:
            owner (AllianceOwner): The owner of the tax account.
            tax_account (AlliancePaymentAccount): The tax account to update.
        """
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.alliance import AllianceOwner

        # Get alliance IDs
        pa_ally_id = tax_account.owner.eve_alliance.alliance_id
        main_ally_id = tax_account.user.profile.main_character.alliance_id

        # Reactivate Account if user returned to alliance
        if tax_account.status == AccountStatus.MISSING and main_ally_id == pa_ally_id:
            self._reset_account(tax_account)
            return

        # Update Account when user left the alliance
        if pa_ally_id != main_ally_id:
            # Mark as missing if not already
            if not tax_account.is_missing:
                self._mark_missing_tax_account(tax_account)
            # Try to move to new alliance if exists
            try:
                new_owner = AllianceOwner.objects.get(
                    eve_alliance__alliance_id=main_ally_id
                )
                # Move to new owner
                self._move_tax_account_to_owner(tax_account, new_owner)
            except AllianceOwner.DoesNotExist:
                pass
            # Save changes
            tax_account.save()

    # pylint: disable=duplicate-code
    def _reset_account(self, tax_account: "PaymentAccountContext"):
        """
        Reset tax account state (unsaved).

        Args:
            tax_account (AlliancePaymentAccount): The tax account to reset.
        """
        tax_account.status = AccountStatus.ACTIVE
        tax_account.notice = None
        tax_account.deposit = 0
        tax_account.last_paid = None
        tax_account.save()
        logger.info(
            "Reset Tax Account %s",
            tax_account.name,
        )

    # pylint: disable=duplicate-code
    def _move_tax_account_to_owner(
        self, tax_account: "PaymentAccountContext", owner: "OwnerContext"
    ):
        """
        Move a tax account to another owner.
        Resets account state.

        Args:
            tax_account (AlliancePaymentAccount): The tax account to move.
            owner (AllianceOwner): The new owner of the tax account.
        """
        tax_account.owner = owner
        tax_account.status = AccountStatus.ACTIVE
        tax_account.notice = None
        tax_account.deposit = 0
        tax_account.last_paid = None
        tax_account.save()
        logger.info(
            "Moved Tax Account %s to Alliance %s",
            tax_account.name,
            owner.eve_alliance.alliance_name,
        )

    # pylint: disable=duplicate-code
    def _mark_missing_tax_account(self, tax_account: "PaymentAccountContext"):
        """
        Mark the tax account as missing (unsaved).

        Args:
            tax_account (AlliancePaymentAccount): The tax account to mark as missing.
        """
        tax_account.status = AccountStatus.MISSING
        tax_account.save()
        logger.info("Marked Tax Account %s as MISSING", tax_account.name)

    @log_timing(logger)
    def check_pay_day(self, owner: "OwnerContext", force_refresh: bool = False) -> None:
        """Check Payments from Account."""
        return owner.update_manager.update_section_if_changed(
            section=AllianceUpdateSection.PAYDAY,
            fetch_func=self._pay_day,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _pay_day(
        self, owner: "OwnerContext", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update Deposits from Account."""
        logger.debug(
            "Updating payday for: %s",
            owner.name,
        )

        tax_accounts = self.filter(owner=owner, status=AccountStatus.ACTIVE)

        for account in tax_accounts:
            if account.last_paid is None:
                # First Period is free
                account.last_paid = timezone.now()
            if timezone.now() - account.last_paid >= timezone.timedelta(
                days=owner.tax_period
            ):
                account.deposit -= owner.tax_amount
                account.last_paid = timezone.now()
                runs = runs + 1
            account.save()

        logger.debug(
            "Finished %s: Payday for %s",
            runs,
            owner.name,
        )

        return ("Finished Payday for %s", owner.name)


class AlliancePaymentManager(models.Manager["PaymentsContext"]):
    @log_timing(logger)
    def update_or_create_payments(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update or Create a Payments entry data."""
        return owner.update_manager.update_section_if_changed(
            section=AllianceUpdateSection.PAYMENTS,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=too-many-locals, unused-argument, duplicate-code
    def _update_or_create_objs(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update or Create payments for Alliance."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.alliance import AlliancePaymentAccount as PaymentAccount
        from taxsystem.models.alliance import AlliancePaymentHistory
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        logger.debug(
            "Updating payments for: %s",
            owner.name,
        )

        tax_accounts = PaymentAccount.objects.filter(owner=owner)

        if not tax_accounts:
            return ("No Payment Users for %s", owner.name)

        users = {}

        # Build Account Map
        for account in tax_accounts:
            account: PaymentAccount
            alts = account.get_alt_ids()
            users[account] = alts

        # Check journal entries for player donations
        journal = CorporationWalletJournalEntry.objects.filter(
            division__corporation=owner.corporation,
            ref_type__in=["player_donation"],
        ).order_by("-date")

        _current_entry_ids = set(
            self.filter(account__owner=owner).values_list("entry_id", flat=True)
        )

        with transaction.atomic():
            items = []
            logs_items = []
            for entry in journal:
                # Skip if already processed
                if entry.entry_id in _current_entry_ids:
                    continue
                for account, alts in users.items():
                    # Check if entry belongs to user's characters
                    if entry.first_party.id in alts:
                        payment_item = self.model(
                            entry_id=entry.entry_id,
                            name=account.name,
                            account=account,
                            amount=entry.amount,
                            request_status=PaymentRequestStatus.PENDING,
                            date=entry.date,
                            reason=entry.reason,
                            owner_id=owner.eve_alliance.alliance_id,
                        )
                        items.append(payment_item)

            # Bulk create payments
            payments = self.bulk_create(
                items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )

            # Create history entries for new payments
            for payment in payments:
                log_items = AlliancePaymentHistory(
                    user=payment.account.user,
                    payment=payment,
                    action=PaymentActions.STATUS_CHANGE,
                    new_status=PaymentRequestStatus.PENDING,
                    comment=PaymentSystemText.ADDED,
                )
                logs_items.append(log_items)

            AlliancePaymentHistory.objects.bulk_create(
                logs_items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )

        logger.debug(
            "Finished %s Payments for %s",
            len(items),
            owner.name,
        )
        return (
            "Finished %s Payments for %s",
            len(items),
            owner.name,
        )

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.app_settings import TAXSYSTEM_BULK_BATCH_SIZE
from taxsystem.constants import AUTH_SELECT_RELATED_MAIN_CHARACTER
from taxsystem.decorators import log_timing
from taxsystem.models.general import CorporationUpdateSection

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.corporation import CorporationOwner, CorporationPaymentAccount

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationAccountManager(models.Manager["CorporationPaymentAccount"]):
    @log_timing(logger)
    def update_or_create_payment_system(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create Payment System data."""
        return owner.update_section_if_changed(
            section=CorporationUpdateSection.PAYMENT_SYSTEM,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _update_or_create_objs(
        self, owner: "CorporationOwner", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update or Create payment system entries from objs data."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.corporation import (
            CorporationFilterSet,
            CorporationPaymentHistory,
            CorporationPayments,
        )

        logger.debug(
            "Updating Payment System for: %s",
            owner.name,
        )

        payments = CorporationPayments.objects.filter(
            account__owner=owner,
            request_status=CorporationPayments.RequestStatus.PENDING,
        )

        _current_payment_ids = set(payments.values_list("id", flat=True))
        _automatic_payment_ids = []

        # Check payment accounts
        self._check_payment_accounts(owner)

        # Check for any automatic payments
        try:
            filters_obj = CorporationFilterSet.objects.filter(owner=owner)
            for filter_obj in filters_obj:
                # Apply filter to pending payments
                payments = filter_obj.filter(payments)
                for payment in payments:
                    if (
                        payment.request_status
                        == CorporationPayments.RequestStatus.PENDING
                    ):
                        # Ensure all transfers are processed in a single transaction
                        with transaction.atomic():
                            payment.request_status = (
                                CorporationPayments.RequestStatus.APPROVED
                            )
                            payment.reviser = "System"

                            # Update payment pool for user
                            self.filter(owner=owner, user=payment.account.user).update(
                                deposit=payment.account.deposit + payment.amount
                            )

                            payment.save()

                            CorporationPaymentHistory(
                                user=payment.account.user,
                                payment=payment,
                                action=CorporationPaymentHistory.Actions.STATUS_CHANGE,
                                new_status=CorporationPayments.RequestStatus.APPROVED,
                                comment=CorporationPaymentHistory.SystemText.AUTOMATIC,
                            ).save()

                            runs = runs + 1
                            _automatic_payment_ids.append(payment.pk)
        except CorporationFilterSet.DoesNotExist:
            pass

        # Check for any payments that need approval
        needs_approval = _current_payment_ids - set(_automatic_payment_ids)
        approvals = CorporationPayments.objects.filter(
            id__in=needs_approval,
            request_status=CorporationPayments.RequestStatus.PENDING,
        )

        for payment in approvals:
            payment.request_status = CorporationPayments.RequestStatus.NEEDS_APPROVAL
            payment.save()

            CorporationPaymentHistory(
                user=payment.account.user,
                payment=payment,
                action=CorporationPaymentHistory.Actions.STATUS_CHANGE,
                new_status=CorporationPayments.RequestStatus.NEEDS_APPROVAL,
                comment=CorporationPaymentHistory.SystemText.REVISER,
            ).save()

            runs = runs + 1

        logger.debug(
            "Finished %s: Payment System entrys for %s",
            runs,
            owner.name,
        )

        return ("Finished Payment System for %s", owner.name)

    def _check_payment_accounts(self, owner: "CorporationOwner"):
        """Check payment accounts for a corporation."""
        logger.debug("Checking Payment Accounts for: %s", owner.name)

        auth_accounts = UserProfile.objects.filter(
            main_character__isnull=False,
        ).select_related(*AUTH_SELECT_RELATED_MAIN_CHARACTER)

        # Clean up orphaned payment accounts
        self._cleanup_orphaned_accounts(owner, auth_accounts)

        if not auth_accounts:
            logger.debug("No valid accounts for skipping Check: %s", owner.name)
            return "No Accounts"

        # Process existing and new accounts
        new_accounts = self._process_accounts(owner, auth_accounts)

        # Bulk create new accounts
        if new_accounts:
            self.bulk_create(
                new_accounts,
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
                ignore_conflicts=True,
            )
            logger.info(
                "Added %s new payment accounts for: %s", len(new_accounts), owner.name
            )
        else:
            logger.debug("No new payment accounts for: %s", owner.name)

        return ("Finished checking Payment Accounts for %s", owner.name)

    def _cleanup_orphaned_accounts(self, owner: "CorporationOwner", auth_accounts):
        """Delete payment accounts for users without main characters."""
        ps_user_ids = self.filter(owner=owner).values_list("user_id", flat=True)
        auth_user_ids = set(auth_accounts.values_list("user_id", flat=True))

        for ps_user_id in ps_user_ids:
            if ps_user_id not in auth_user_ids:
                self.filter(owner=owner, user_id=ps_user_id).delete()
                logger.info(
                    "Deleted Payment Account for user id: %s from Corporation: %s",
                    ps_user_id,
                    owner.name,
                )

    def _process_accounts(self, owner: "CorporationOwner", auth_accounts):
        """Process existing payment accounts and return list of new accounts to create."""
        new_accounts = []

        for account in auth_accounts:
            main = account.main_character
            try:
                payment_account = self.model.objects.get(user=account.user)
                self._update_existing_account(owner, payment_account, main)
            except self.model.DoesNotExist:
                logger.debug(
                    "Creating new payment account for user: %s", account.user.username
                )
                new_accounts.append(
                    self.model(
                        name=main.character_name,
                        owner=owner,
                        user=account.user,
                        status=self.model.Status.ACTIVE,
                    )
                )

        return new_accounts

    def _update_existing_account(
        self, owner: "CorporationOwner", payment_account, main
    ):
        """Update an existing payment account based on current state."""
        pa_corporation_id = payment_account.owner.eve_corporation.corporation_id
        main_corp_id = main.corporation_id

        # Handle owner change
        if payment_account.owner != owner:
            payment_account.owner = owner
            payment_account.deposit = 0
            payment_account.save()
            logger.info(
                "Moved Payment Account %s to Corporation %s",
                payment_account.name,
                owner.eve_corporation.corporation_name,
            )

        # Reactivate if not deactivated
        if payment_account.status != self.model.Status.DEACTIVATED:
            payment_account.status = self.model.Status.ACTIVE
            payment_account.save()

        # Handle corporation changes
        if pa_corporation_id != main_corp_id:
            self._handle_corporation_change(payment_account, main_corp_id)
        elif payment_account.is_missing:
            self._reactivate_missing_account(payment_account)

    def _handle_corporation_change(self, payment_account, main_corp_id):
        """Handle payment account when user changes corporation."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.corporation import CorporationOwner as CorpOwner

        if not payment_account.is_missing:
            # Mark as missing if left corporation
            payment_account.status = self.model.Status.MISSING
            payment_account.save()
            logger.info("Marked Payment Account %s as MISSING", payment_account.name)
        else:
            # Try to move to new corporation
            try:
                new_owner = CorpOwner.objects.get(
                    eve_corporation__corporation_id=main_corp_id
                )
                payment_account.owner = new_owner
                payment_account.deposit = 0
                payment_account.status = self.model.Status.ACTIVE
                payment_account.last_paid = None
                payment_account.save()
                logger.info(
                    "Moved Payment Account %s to Corporation %s",
                    payment_account.name,
                    new_owner.eve_corporation.corporation_name,
                )
            except CorpOwner.DoesNotExist:
                pass

    def _reactivate_missing_account(self, payment_account):
        """Reactivate a missing payment account when user returns."""
        payment_account.status = self.model.Status.ACTIVE
        payment_account.notice = None
        payment_account.deposit = 0
        payment_account.last_paid = None
        payment_account.save()
        logger.info(
            "Reactivated Payment Account %s is back in Corporation %s",
            payment_account.name,
            payment_account.owner.eve_corporation.corporation_name,
        )

    @log_timing(logger)
    def check_pay_day(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Check Payments from Account."""
        return owner.update_section_if_changed(
            section=CorporationUpdateSection.PAYDAY,
            fetch_func=self._pay_day,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _pay_day(
        self, owner: "CorporationOwner", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update Deposits from Account."""
        logger.debug(
            "Updating payday for: %s",
            owner.name,
        )

        payment_system = self.filter(owner=owner, status=self.model.Status.ACTIVE)

        for user in payment_system:
            if user.last_paid is None:
                # First Period is free
                user.last_paid = timezone.now()
            if timezone.now() - user.last_paid >= timezone.timedelta(
                days=owner.tax_period
            ):
                user.deposit -= owner.tax_amount
                user.last_paid = timezone.now()
                runs = runs + 1
            user.save()

        logger.debug(
            "Finished %s: Payday for %s",
            runs,
            owner.name,
        )

        return ("Finished Payday for %s", owner.name)


class PaymentsManager(models.Manager):
    @log_timing(logger)
    def update_or_create_payments(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a Payments entry data."""
        return owner.update_section_if_changed(
            section=CorporationUpdateSection.PAYMENTS,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=too-many-locals, unused-argument
    def _update_or_create_objs(
        self, owner: "CorporationOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create payment system entries from objs data."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.corporation import (
            CorporationPaymentAccount as PaymentAccount,
        )
        from taxsystem.models.corporation import (
            CorporationPaymentHistory,
            CorporationPayments,
        )
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        logger.debug(
            "Updating payments for: %s",
            owner.name,
        )

        payment_accounts = PaymentAccount.objects.filter(owner=owner)

        if not payment_accounts:
            return ("No Payment Users for %s", owner.name)

        users = {}

        for account in payment_accounts:
            account: PaymentAccount
            alts = account.get_alt_ids()
            users[account] = alts

        journal = CorporationWalletJournalEntry.objects.filter(
            division__corporation=owner, ref_type__in=["player_donation"]
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
                    if entry.first_party.id in alts:
                        payment_item = CorporationPayments(
                            entry_id=entry.entry_id,
                            name=account.name,
                            account=account,
                            amount=entry.amount,
                            request_status=CorporationPayments.RequestStatus.PENDING,
                            date=entry.date,
                            reason=entry.reason,
                            owner_id=owner.eve_corporation.corporation_id,
                        )
                        items.append(payment_item)

            payments = self.bulk_create(
                items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )

            for payment in payments:
                # Only log created payments
                payment_obj = self.filter(
                    entry_id=payment.entry_id,
                    account=payment.account,
                    owner_id=owner.eve_corporation.corporation_id,
                ).first()

                if not payment_obj:
                    continue

                log_items = CorporationPaymentHistory(
                    user=payment_obj.account.user,
                    payment=payment_obj,
                    action=CorporationPaymentHistory.Actions.STATUS_CHANGE,
                    new_status=CorporationPayments.RequestStatus.PENDING,
                    comment=CorporationPaymentHistory.SystemText.ADDED,
                )
                logs_items.append(log_items)

            CorporationPaymentHistory.objects.bulk_create(
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

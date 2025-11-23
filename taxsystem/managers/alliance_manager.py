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
from taxsystem.decorators import log_timing
from taxsystem.managers.base import BaseOwnerQuerySet
from taxsystem.models.general import AllianceUpdateSection

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.alliance import (
        AllianceOwner,
        AlliancePaymentAccount,
        AlliancePayments,
    )


# pylint: disable=duplicate-code
class AllianceOwnerQuerySet(BaseOwnerQuerySet):
    """QuerySet for AllianceOwner with common filtering logic."""

    # Configure base class for alliance-specific behavior
    owner_type = "alliance"
    permission_prefix = "taxsystem.manage_alliances"
    owner_field = "alliance_id"  # Field on EveCharacter
    owner_model_field = "eve_alliance__alliance_id"  # Field on AllianceOwner model
    own_permission = "taxsystem.manage_own_alliance"
    update_status_relation = "ts_alliance_update_status"
    update_section_class = AllianceUpdateSection


class AllianceOwnerManager(models.Manager["AllianceOwner"]):
    def get_queryset(self):
        return AllianceOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)


class AlliancePaymentAccountManager(models.Manager["AlliancePaymentAccount"]):
    @log_timing(logger)
    def update_or_create_payment_system(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create Payment System data."""
        return owner.update_section_if_changed(
            section=AllianceUpdateSection.PAYMENT_SYSTEM,
            fetch_func=self._update_payment_accounts,
            force_refresh=force_refresh,
        )

    # pylint: disable=unused-argument, duplicate-code
    @transaction.atomic()
    def _update_payment_accounts(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Update payment accounts for a alliance."""
        logger.debug(
            "Updating Payment Accounts for: %s",
            owner.name,
        )

        # Get all accounts of the alliance
        accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__alliance_id=owner.eve_alliance.alliance_id,
        ).select_related(
            "user__profile__main_character",
            "main_character__character_ownership",
            "main_character__character_ownership__user__profile",
            "main_character__character_ownership__user__profile__main_character",
        )

        if not accounts:
            logger.debug("No valid accounts for: %s", owner.name)
            return "No Accounts"

        items = []

        logger.debug(
            "Found %s accounts for alliance: %s",
            accounts.count(),
            owner.name,
        )

        for account in accounts:
            main = account.main_character
            try:
                # Check existing payment account for user
                existing_payment_account = self.model.objects.get(user=account.user)
                if existing_payment_account.owner != owner:
                    # Move payment account to new alliance if changed
                    existing_payment_account.owner = owner
                    existing_payment_account.deposit = 0
                    existing_payment_account.save()
                    logger.info(
                        "Moved Payment Account %s to Alliance %s",
                        existing_payment_account.name,
                        owner.eve_alliance.alliance_name,
                    )
                if existing_payment_account.status != self.model.Status.DEACTIVATED:
                    # Reactivate payment account if not deactivated
                    existing_payment_account.status = self.model.Status.ACTIVE
                    existing_payment_account.save()
            except self.model.DoesNotExist:
                logger.debug(
                    "Creating new payment account for user: %s",
                    account.user.username,
                )
                # Create new payment account
                items.append(
                    self.model(
                        name=main.character_name,
                        owner=owner,
                        user=account.user,
                        status=self.model.Status.ACTIVE,
                    )
                )

        if items:
            self.bulk_create(items, ignore_conflicts=True)
            logger.info(
                "Added %s new payment accounts for: %s",
                len(items),
                owner.name,
            )
        else:
            logger.debug(
                "No new payment accounts for: %s",
                owner.name,
            )

        self._check_payment_accounts(owner, accounts)

        return (
            "Finished payment account for %s",
            owner.name,
        )

    @log_timing(logger)
    def _check_payment_accounts(
        self, owner: "AllianceOwner", accounts: models.QuerySet[UserProfile]
    ) -> None:
        """Check payment accounts status for a alliance."""
        # pylint: disable=import-outside-toplevel
        # AA TaxSystem
        from taxsystem.models.alliance import AllianceOwner

        logger.debug(
            "Checking Payment Accounts for: %s",
            owner.name,
        )

        for account in accounts:
            # Check existing payment account
            try:
                payment_account = self.model.objects.get(user=account.user)
            except self.model.DoesNotExist:
                continue

            # Get Main Alliance ID
            main_alliance_id = account.main_character.alliance_id
            # Get Payment Account Alliance ID
            pa_alliance_id = payment_account.owner.eve_alliance.alliance_id

            # If account no longer in alliance, mark as missing
            if (
                not payment_account.is_missing
                and not pa_alliance_id == main_alliance_id
            ):
                payment_account.status = self.model.Status.MISSING
                payment_account.save()
                logger.info(
                    "Marked Payment Account %s as MISSING",
                    payment_account.name,
                )
            # If account has changed alliance, update payment account
            elif payment_account.is_missing and pa_alliance_id != main_alliance_id:
                try:
                    new_owner = AllianceOwner.objects.get(
                        eve_alliance__alliance_id=main_alliance_id
                    )
                    payment_account.owner = new_owner
                    payment_account.deposit = 0
                    payment_account.status = self.model.Status.ACTIVE
                    payment_account.last_paid = None
                    payment_account.save()
                    logger.info(
                        "Moved Payment Account %s to Alliance %s",
                        payment_account.name,
                        new_owner.eve_alliance.alliance_name,
                    )
                except AllianceOwner.DoesNotExist:
                    continue
            # If account is back in alliance, reactivate payment account
            elif payment_account.is_missing and pa_alliance_id == main_alliance_id:
                payment_account.status = self.model.Status.ACTIVE
                payment_account.notice = None
                payment_account.deposit = 0
                payment_account.last_paid = None
                payment_account.save()
                logger.info(
                    "Reactivated Payment Account %s for Alliance %s",
                    payment_account.name,
                    owner.eve_alliance.alliance_name,
                )
        return (
            "Finished checking payment Accounts for %s",
            owner.name,
        )

    @log_timing(logger)
    def check_pay_day(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Check Payments from Account."""
        return owner.update_section_if_changed(
            section=AllianceUpdateSection.PAYDAY,
            fetch_func=self._pay_day,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _pay_day(
        self, owner: "AllianceOwner", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update Deposits from Account."""
        logger.debug(
            "Updating payday for: %s",
            owner.name,
        )

        payment_accounts = self.filter(owner=owner, status=self.model.Status.ACTIVE)

        for account in payment_accounts:
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


class AlliancePaymentManager(models.Manager["AlliancePayments"]):
    @log_timing(logger)
    def update_or_create_payments(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create a Payments entry data."""
        return owner.update_section_if_changed(
            section=AllianceUpdateSection.PAYMENTS,
            fetch_func=self._update_or_create_payments,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=too-many-locals, unused-argument
    def _update_or_create_payments(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create payments for Alliance."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.alliance import AlliancePaymentAccount as PaymentAccount
        from taxsystem.models.alliance import (
            AlliancePaymentHistory,
        )
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        logger.debug(
            "Updating payments for: %s",
            owner.name,
        )

        accounts = PaymentAccount.objects.filter(owner=owner)

        if not accounts:
            return ("No Payment Users for %s", owner.name)

        users = {}

        for user in accounts:
            user: PaymentAccount
            alts = user.get_alt_ids()
            users[user] = alts

        # Check journal entries for player donations
        journal = CorporationWalletJournalEntry.objects.filter(
            division__corporation__eve_corporation=owner.corporation.eve_corporation,
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
                for user, alts in users.items():
                    if entry.first_party.id in alts:
                        payment_item = self.model(
                            entry_id=entry.entry_id,
                            name=user.name,
                            account=user,
                            amount=entry.amount,
                            request_status=self.model.RequestStatus.PENDING,
                            date=entry.date,
                            reason=entry.reason,
                            owner_id=owner.eve_alliance.alliance_id,
                        )
                        items.append(payment_item)

            payments = self.bulk_create(items, ignore_conflicts=True)

            # Create history entries
            for payment in payments:
                # After bulk_create with ignore_conflicts, we need to fetch the actual object
                # Use filter().first() to avoid MultipleObjectsReturned
                payment_obj = self.filter(
                    entry_id=payment.entry_id,
                    account=payment.account,
                    owner_id=owner.eve_alliance.alliance_id,
                ).first()

                if not payment_obj:
                    continue

                log_items = AlliancePaymentHistory(
                    user=payment_obj.account.user,
                    payment=payment_obj,
                    action=AlliancePaymentHistory.Actions.STATUS_CHANGE,
                    new_status=self.model.RequestStatus.PENDING,
                    comment=AlliancePaymentHistory.SystemText.ADDED,
                )
                logs_items.append(log_items)

            AlliancePaymentHistory.objects.bulk_create(
                logs_items, ignore_conflicts=True
            )

        # Check for system payments
        self._check_system_payments(owner)

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

    # pylint: disable=unused-argument
    def _check_system_payments(self, owner: "AllianceOwner", runs: int = 0) -> None:
        """Check for automatic system payments that has been approved by Filter Set from Alliance."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.alliance import (
            AllianceFilterSet,
        )
        from taxsystem.models.alliance import AlliancePaymentAccount as PaymentAccount
        from taxsystem.models.alliance import (
            AlliancePaymentHistory,
        )

        logger.debug(
            "Checking automatic Payments for: %s",
            owner.name,
        )

        payments = self.filter(
            account__owner=owner,
            request_status=self.model.RequestStatus.PENDING,
        )

        _current_payment_ids = set(payments.values_list("id", flat=True))
        _automatic_payment_ids = []

        # Check for any automatic payments
        try:
            filter_sets = AllianceFilterSet.objects.filter(owner=owner)

            # Iterate through each filter set
            for filter_set in filter_sets:
                # Apply the filter set filters to the payments queryset
                payments = filter_set.filter(payments)
                # Iterate through the filtered payments
                for payment in payments:
                    if payment.request_status == self.model.RequestStatus.PENDING:
                        # Ensure all transfers are processed in a single transaction
                        with transaction.atomic():
                            payment.request_status = self.model.RequestStatus.APPROVED
                            payment.reviser = "System"

                            # Update payment pool for user
                            PaymentAccount.objects.filter(
                                owner=owner, user=payment.account.user
                            ).update(deposit=payment.account.deposit + payment.amount)

                            payment.save()

                            AlliancePaymentHistory(
                                user=payment.account.user,
                                payment=payment,
                                action=AlliancePaymentHistory.Actions.STATUS_CHANGE,
                                new_status=self.model.RequestStatus.APPROVED,
                                comment=AlliancePaymentHistory.SystemText.AUTOMATIC,
                            ).save()

                            runs = runs + 1
                            _automatic_payment_ids.append(payment.pk)
        except AllianceFilterSet.DoesNotExist:
            pass

        # Check for any payments that need approval
        needs_approval = _current_payment_ids - set(_automatic_payment_ids)
        approvals = self.model.objects.filter(
            id__in=needs_approval,
            request_status=self.model.RequestStatus.PENDING,
        )

        # Update payments to NEEDS_APPROVAL
        for payment in approvals:
            payment.request_status = self.model.RequestStatus.NEEDS_APPROVAL
            payment.save()

            AlliancePaymentHistory(
                user=payment.account.user,
                payment=payment,
                action=AlliancePaymentHistory.Actions.STATUS_CHANGE,
                new_status=self.model.RequestStatus.NEEDS_APPROVAL,
                comment=AlliancePaymentHistory.SystemText.REVISER,
            ).save()

        logger.debug(
            "Finished %s: Automatic Payments for %s",
            runs,
            owner.name,
        )

        return ("Finished Payment System for %s", owner.name)

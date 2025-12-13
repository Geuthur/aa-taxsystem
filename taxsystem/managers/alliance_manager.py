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
    from taxsystem.models.alliance import (
        AllianceOwner,
        AlliancePaymentAccount,
        AlliancePayments,
    )


# pylint: disable=duplicate-code
class AllianceOwnerQuerySet(models.QuerySet["AllianceOwner"]):
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


class AllianceOwnerManager(models.Manager["AllianceOwner"]):
    def get_queryset(self):
        return AllianceOwnerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)

    def annotate_total_update_status(self):
        return self.get_queryset().annotate_total_update_status()


class AlliancePaymentAccountManager(models.Manager["AlliancePaymentAccount"]):
    @log_timing(logger)
    def update_or_create_payment_system(
        self, owner: "AllianceOwner", force_refresh: bool = False
    ) -> None:
        """Update or Create Payment System data."""
        return owner.update_manager.update_section_if_changed(
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
                if existing_payment_account.status != AccountStatus.DEACTIVATED:
                    # Reactivate payment account if not deactivated
                    existing_payment_account.status = AccountStatus.ACTIVE
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
                        status=AccountStatus.ACTIVE,
                    )
                )

        if items:
            self.bulk_create(
                items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )
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
                payment_account.status = AccountStatus.MISSING
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
                    payment_account.status = AccountStatus.ACTIVE
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
                payment_account.status = AccountStatus.ACTIVE
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
        return owner.update_manager.update_section_if_changed(
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

        payment_accounts = self.filter(owner=owner, status=AccountStatus.ACTIVE)

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
        return owner.update_manager.update_section_if_changed(
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
        from taxsystem.models.logs import (
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
                            request_status=PaymentRequestStatus.PENDING,
                            date=entry.date,
                            reason=entry.reason,
                            owner_id=owner.eve_alliance.alliance_id,
                        )
                        items.append(payment_item)

            payments = self.bulk_create(
                items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )

            # Create history entries
            for payment in payments:
                # Only log created payments
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
                    action=PaymentActions.STATUS_CHANGE,
                    new_status=PaymentRequestStatus.PENDING,
                    comment=PaymentSystemText.ADDED,
                )
                logs_items.append(log_items)

            AlliancePaymentHistory.objects.bulk_create(
                logs_items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
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
        from taxsystem.models.logs import (
            AlliancePaymentHistory,
        )

        logger.debug(
            "Checking automatic Payments for: %s",
            owner.name,
        )

        payments = self.filter(
            account__owner=owner,
            request_status=PaymentRequestStatus.PENDING,
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
                    if payment.request_status == PaymentRequestStatus.PENDING:
                        # Ensure all transfers are processed in a single transaction
                        with transaction.atomic():
                            payment.request_status = PaymentRequestStatus.APPROVED
                            payment.reviser = "System"

                            # Update payment pool for user
                            PaymentAccount.objects.filter(
                                owner=owner, user=payment.account.user
                            ).update(deposit=payment.account.deposit + payment.amount)

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
        approvals = self.model.objects.filter(
            id__in=needs_approval,
            request_status=PaymentRequestStatus.PENDING,
        )

        # Update payments to NEEDS_APPROVAL
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

        logger.debug(
            "Finished %s: Automatic Payments for %s",
            runs,
            owner.name,
        )

        return ("Finished Payment System for %s", owner.name)

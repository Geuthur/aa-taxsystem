# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA TaxSystem
from taxsystem import __title__
from taxsystem.decorators import log_timing
from taxsystem.models.general import CorporationUpdateSection

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.corporation import CorporationOwner

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CorporationAccountManager(models.Manager):
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

        # Check for any automatic payments
        try:
            filters_obj = CorporationFilterSet.objects.filter(owner=owner)
            for filter_obj in filters_obj:
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
            CorporationPaymentAccount,
            CorporationPaymentHistory,
            CorporationPayments,
        )
        from taxsystem.models.wallet import CorporationWalletJournalEntry

        logger.debug(
            "Updating payments for: %s",
            owner.name,
        )

        accounts = CorporationPaymentAccount.objects.filter(owner=owner)

        if not accounts:
            return ("No Payment Users for %s", owner.name)

        users = {}

        for user in accounts:
            user: CorporationPaymentAccount
            alts = user.get_alt_ids()
            users[user] = alts

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
                for user, alts in users.items():
                    if entry.first_party.id in alts:
                        payment_item = CorporationPayments(
                            entry_id=entry.entry_id,
                            name=user.name,
                            account=user,
                            amount=entry.amount,
                            request_status=CorporationPayments.RequestStatus.PENDING,
                            date=entry.date,
                            reason=entry.reason,
                        )
                        items.append(payment_item)

            payments = self.bulk_create(items, ignore_conflicts=True)

            for payment in payments:
                try:
                    payment = self.get(
                        entry_id=payment.entry_id, account=payment.account
                    )
                except CorporationPayments.DoesNotExist:
                    continue

                log_items = CorporationPaymentHistory(
                    user=payment.account.user,
                    payment=payment,
                    action=CorporationPaymentHistory.Actions.STATUS_CHANGE,
                    new_status=CorporationPayments.RequestStatus.PENDING,
                    comment=CorporationPaymentHistory.SystemText.ADDED,
                )
                logs_items.append(log_items)

            CorporationPaymentHistory.objects.bulk_create(
                logs_items, ignore_conflicts=True
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

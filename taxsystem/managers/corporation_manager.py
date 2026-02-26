# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import User, UserProfile
from allianceauth.services.hooks import get_extension_logger

# AA TaxSystem
from taxsystem import __title__
from taxsystem.app_settings import TAXSYSTEM_BULK_BATCH_SIZE
from taxsystem.decorators import log_timing
from taxsystem.models.general import EveEntity, UpdateSectionResult
from taxsystem.models.helpers.textchoices import (
    AccountStatus,
    CorporationUpdateSection,
    PaymentActions,
    PaymentRequestStatus,
    PaymentSystemText,
)
from taxsystem.providers import AppLogger, esi

logger = AppLogger(get_extension_logger(__name__), __title__)

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import (
        CorporationsCorporationIdMembertrackingGetItem as CorporationMemberTrackingContext,
    )

    # AA TaxSystem
    from taxsystem.models.corporation import CorporationOwner as OwnerContext
    from taxsystem.models.corporation import (
        CorporationPaymentAccount as PaymentAccountContext,
    )
    from taxsystem.models.corporation import CorporationPayments as PaymentsContext
    from taxsystem.models.corporation import Members as MembersContext


class CorporationAccountManager(models.Manager["PaymentAccountContext"]):
    @log_timing(logger)
    def update_or_create_tax_accounts(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> UpdateSectionResult:
        """Update or Create Tax Accounts data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.TAX_ACCOUNTS,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument, too-many-locals
    def _update_or_create_objs(
        self, owner: "OwnerContext", force_refresh: bool = False, runs: int = 0
    ) -> None:
        """Update or Create tax accounts entries from objs data."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.corporation import (
            CorporationFilterSet,
            CorporationPaymentHistory,
            CorporationPayments,
        )

        # TODO Create a Hash Tag to track changes better
        logger.debug(
            "Updating Tax Accounts for: %s",
            owner.name,
        )

        payments = CorporationPayments.objects.filter(
            account__owner=owner,
            request_status__in=[
                PaymentRequestStatus.PENDING,
                PaymentRequestStatus.NEEDS_APPROVAL,
            ],
        )

        _current_payment_ids = set(payments.values_list("id", flat=True))
        _automatic_payment_ids = []

        # Check tax accounts before we process payments
        self._check_tax_accounts(owner)

        # Check for any automatic payments
        filters_obj = CorporationFilterSet.objects.filter(owner=owner)
        for filter_obj in filters_obj:
            f_payments = filter_obj.filter(payments)
            for payment in f_payments:
                # Process only pending or needs approval payments
                if payment.request_status in [
                    PaymentRequestStatus.PENDING,
                    PaymentRequestStatus.NEEDS_APPROVAL,
                ]:
                    # Ensure all transfers are processed in a single transaction
                    with transaction.atomic():
                        payment.request_status = PaymentRequestStatus.APPROVED
                        payment.reviser = "System"

                        # Update payment pool for user
                        self.filter(owner=owner, user=payment.account.user).update(
                            deposit=payment.account.deposit + payment.amount
                        )

                        payment.save()

                        CorporationPaymentHistory(
                            user=payment.account.user,
                            payment=payment,
                            action=PaymentActions.STATUS_CHANGE,
                            new_status=PaymentRequestStatus.APPROVED,
                            comment=PaymentSystemText.AUTOMATIC,
                        ).save()

                        runs = runs + 1
                        _automatic_payment_ids.append(payment.pk)

        # Check for any payments that need approval
        needs_approval = _current_payment_ids - set(_automatic_payment_ids)
        approvals = CorporationPayments.objects.filter(
            id__in=needs_approval,
            request_status=PaymentRequestStatus.PENDING,
        )

        for payment in approvals:
            payment.request_status = PaymentRequestStatus.NEEDS_APPROVAL
            payment.save()

            CorporationPaymentHistory(
                user=payment.account.user,
                payment=payment,
                action=PaymentActions.STATUS_CHANGE,
                new_status=PaymentRequestStatus.NEEDS_APPROVAL,
                comment=PaymentSystemText.REVISER,
            ).save()

            runs = runs + 1

        logger.debug(
            "Finished %s: Tax Account entrys for %s",
            runs,
            owner.name,
        )

        return ("Finished Tax Accounts for %s", owner.name)

    def _check_tax_accounts(self, owner: "OwnerContext"):
        """
        Check tax accounts for a corporation.
        Create new accounts, update existing ones, and remove orphaned accounts.
        """
        logger.debug("Checking Tax Accounts for: %s", owner.name)
        items = []

        # Get all existing accounts with a Main Character
        auth_accounts = UserProfile.objects.filter(
            main_character__isnull=False,
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
                "Creating new corporation tax account for user: %s",
                account.user.username,
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

    def _cleanup_orphaned_accounts(
        self, owner: "OwnerContext", auth_user_ids: set, ps_user_ids: set
    ):
        """Delete Tax accounts for users without main characters."""
        for ps_user_id in ps_user_ids:
            if ps_user_id not in auth_user_ids:
                self.filter(owner=owner, user_id=ps_user_id).delete()
                logger.info(
                    "Deleted Tax Account for user id: %s from Corporation: %s",
                    ps_user_id,
                    owner.name,
                )

    def _update_existing_account(
        self,
        tax_account: "PaymentAccountContext",
    ):
        """
        Update an existing tax account based on current state.

        Args:
            owner (CorporationOwner): The owner of the tax account.
            tax_account (CorporationPaymentAccount): The tax account to update.
        """
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA TaxSystem
        from taxsystem.models.corporation import CorporationOwner

        # Get corporation IDs
        pa_corp_id = tax_account.owner.eve_corporation.corporation_id
        main_corp_id = tax_account.user.profile.main_character.corporation_id

        # Reactivate Account if user returned to corporation
        if tax_account.status == AccountStatus.MISSING and main_corp_id == pa_corp_id:
            self._reset_account(tax_account)
            return

        # Update Account when user left the corporation
        if pa_corp_id != main_corp_id:
            # Mark as missing if not already
            if not tax_account.is_missing:
                self._mark_missing_tax_account(tax_account)
            # Try to move to new corporation if exists
            try:
                new_owner = CorporationOwner.objects.get(
                    eve_corporation__corporation_id=main_corp_id
                )
                # Move to new owner
                self._move_tax_account_to_owner(tax_account, new_owner)
            except CorporationOwner.DoesNotExist:
                pass
            # Save changes
            tax_account.save()

    def _reset_account(self, tax_account: "PaymentAccountContext"):
        """
        Reset tax account state (unsaved).

        Args:
            tax_account (CorporationPaymentAccount): The tax account to reset.
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

    def _move_tax_account_to_owner(
        self, tax_account: "PaymentAccountContext", owner: "OwnerContext"
    ):
        """
        Move a tax account to another owner.
        Resets account state.

        Args:
            tax_account (CorporationPaymentAccount): The tax account to move.
            owner (CorporationOwner): The new owner of the tax account.
        """
        tax_account.owner = owner
        tax_account.status = AccountStatus.ACTIVE
        tax_account.notice = None
        tax_account.deposit = 0
        tax_account.last_paid = None
        tax_account.save()
        logger.info(
            "Moved Tax Account %s to Corporation %s",
            tax_account.name,
            owner.eve_corporation.corporation_name,
        )

    def _mark_missing_tax_account(self, tax_account: "PaymentAccountContext"):
        """
        Mark the tax account as missing (unsaved).

        Args:
            tax_account (CorporationPaymentAccount): The tax account to mark as missing.
        """
        tax_account.status = AccountStatus.MISSING
        tax_account.save()
        logger.info("Marked Tax Account %s as MISSING", tax_account.name)

    @log_timing(logger)
    def check_payment_deadlines(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> UpdateSectionResult:
        """
        Checking payment deadlines for Corporation.
        This will deduct tax amounts from deposits if payment period has passed.
        """
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.DEADLINES,
            fetch_func=self._payment_deadlines,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=unused-argument
    def _payment_deadlines(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update Deposits from Account."""
        logger.debug(
            "Updating payment deadlines for: %s",
            owner.name,
        )

        tax_accounts = self.filter(owner=owner, status=AccountStatus.ACTIVE)

        items = []
        for account in tax_accounts:
            if account.last_paid is None:
                # First Period is free
                account.last_paid = timezone.now()
            if timezone.now() - account.last_paid >= timezone.timedelta(
                days=owner.tax_period
            ):
                account.deposit -= owner.tax_amount
                account.last_paid = timezone.now()
            items.append(account)

        if not items:
            logger.debug("No new payment deadlines for: %s", owner.name)
            return ("No new payment deadlines for %s", owner.name)

        self.bulk_update(
            items,
            ["deposit", "last_paid"],
            batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
        )

        logger.debug(
            "Finished %s: payment deadlines for %s",
            len(items),
            owner.name,
        )

        return ("Finished payment deadlines for %s", owner.name)


class PaymentsQuerySet(models.QuerySet["PaymentsContext"]):
    # pylint: disable=duplicate-code
    def visible_to(self, user: User):
        """Return visible payments for the user depending on their permissions."""
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all payments for superuser %s.",
                user,
            )
            return self

        if user.has_perm("taxsystem.manage_corps"):
            logger.debug(
                "Returning all corporation payments for Tax Audit Manager %s.", user
            )
            return self
        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(account__user=user)]
            if user.has_perm("taxsystem.manage_own_corp"):
                corp_ids = user.character_ownerships.all().values_list(
                    "character__corporation_id", flat=True
                )
                queries.append(
                    models.Q(owner__eve_corporation__corporation_id__in=corp_ids)
                )

            logger.debug(
                "%s queries for user %s visible corporation.", len(queries), user
            )

            if len(queries) == 0:
                return self.none()

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def visible_open_invoices(self, user: User) -> int | None:
        """
        Get the count of visible invoices for the given user.
        """
        owners = self.visible_to(user=user)
        return owners.filter(
            request_status__in=[
                PaymentRequestStatus.PENDING,
                PaymentRequestStatus.NEEDS_APPROVAL,
            ],
        ).count()

    def open_invoices(self, owner: "OwnerContext") -> int | None:
        """
        Get open invoices for the given owner.
        """
        return self.filter(
            owner=owner,
            request_status__in=[
                PaymentRequestStatus.PENDING,
                PaymentRequestStatus.NEEDS_APPROVAL,
            ],
        ).count()


class PaymentsManager(models.Manager["PaymentsContext"]):
    def get_queryset(self):
        return PaymentsQuerySet(self.model, using=self._db)

    def get_visible(self, user: User):
        return self.get_queryset().visible_to(user=user)

    def get_visible_open_invoices(self, user: User):
        """Get the count of visible open invoices for the given user."""
        return self.get_queryset().visible_open_invoices(user=user)

    def get_owner_open_invoices(self, user: User, owner: "OwnerContext"):
        """Get the count of open invoices for the given user and owner."""
        if user.has_perm("taxsystem.manage_own_corp") or user.has_perm(
            "taxsystem.manage_corps"
        ):
            return self.get_queryset().open_invoices(owner=owner)
        return 0

    @log_timing(logger)
    def update_or_create_payments(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> UpdateSectionResult:
        """Update or Create a Payments entry data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.PAYMENTS,
            fetch_func=self._update_or_create_objs,
            force_refresh=force_refresh,
        )

    @transaction.atomic()
    # pylint: disable=too-many-locals, unused-argument
    def _update_or_create_objs(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update or Create payment for Corporation."""
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

        tax_accounts = PaymentAccount.objects.filter(owner=owner)

        if not tax_accounts:
            return ("No Payment Users for %s", owner.name)

        users = {}

        # Build Account Map
        for account in tax_accounts:
            account: PaymentAccount
            alts = account.get_alt_ids()
            users[account] = alts

        journal_qs = CorporationWalletJournalEntry.objects.filter(
            division__corporation=owner, ref_type__in=["player_donation"]
        ).order_by("-date")

        _current_entry_ids = set(
            self.filter(account__owner=owner).values_list(
                "journal__entry_id", flat=True
            )
        )
        with transaction.atomic():
            items = []
            logs_items = []
            for journal in journal_qs:
                # Skip if already processed
                if journal.entry_id in _current_entry_ids:
                    continue
                for account, alts in users.items():
                    if journal.first_party.id in alts:
                        payment_item = CorporationPayments(
                            owner=owner,
                            journal=journal,
                            name=account.name,
                            account=account,
                            amount=journal.amount,
                            request_status=PaymentRequestStatus.PENDING,
                            date=journal.date,
                            reason=journal.reason,
                        )
                        items.append(payment_item)

            if not items:
                logger.debug("No new Payments for: %s", owner.name)
                return ("No new Payments for %s", owner.name)

            # Bulk create payments
            payments = self.bulk_create(
                items, batch_size=TAXSYSTEM_BULK_BATCH_SIZE, ignore_conflicts=True
            )

            for payment in payments:
                # Only log created payments
                payment_obj = self.filter(
                    journal=payment.journal,
                    account=payment.account,
                    owner=owner,
                ).first()

                if not payment_obj:
                    continue

                log_items = CorporationPaymentHistory(
                    user=payment_obj.account.user,
                    payment=payment_obj,
                    action=PaymentActions.STATUS_CHANGE,
                    new_status=PaymentRequestStatus.PENDING,
                    comment=PaymentSystemText.ADDED,
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


class MembersManager(models.Manager["MembersContext"]):
    @log_timing(logger)
    def update_or_create_esi(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Update or Create a Members from ESI data."""
        return owner.update_manager.update_section_if_changed(
            section=CorporationUpdateSection.MEMBERS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, owner: "OwnerContext", force_refresh: bool = False
    ) -> None:
        """Fetch Members entries from ESI data."""
        req_scopes = [
            "esi-corporations.read_corporation_membership.v1",
            "esi-corporations.track_members.v1",
        ]
        req_roles = ["CEO", "Director"]

        token = owner.get_token(scopes=req_scopes, req_roles=req_roles)

        # Make the ESI request
        members_ob = esi.client.Corporation.GetCorporationsCorporationIdMembertracking(
            corporation_id=owner.eve_corporation.corporation_id,
            token=token,
        )

        members_items, response = members_ob.results(
            return_response=True, force_refresh=force_refresh
        )
        logger.debug("ESI response Status: %s", response.status_code)

        self._update_or_create_objs(owner=owner, objs=members_items)

    @transaction.atomic()
    # pylint: disable=too-many-locals
    def _update_or_create_objs(
        self,
        owner: "OwnerContext",
        objs: list["CorporationMemberTrackingContext"],
    ) -> None:
        """Update or Create Members entries from objs data."""
        logger.info("Updating Members for: %s", owner.name)

        _current_members_ids = set(
            self.filter(owner=owner).values_list("character_id", flat=True)
        )
        _esi_members_ids = [member.character_id for member in objs]
        _old_members = []
        _new_members = []

        characters = EveEntity.objects.bulk_resolve_names(ids=_esi_members_ids)
        for member in objs:
            character_id = member.character_id
            joined = member.start_date
            logon_date = member.logon_date
            logged_off = member.logoff_date
            character_name = characters.to_name(character_id)
            member_item = self.model(
                owner=owner,
                character_id=character_id,
                character_name=character_name,
                joined=joined,
                logon=logon_date,
                logged_off=logged_off,
                status=self.model.States.ACTIVE,
            )
            if character_id in _current_members_ids:
                _old_members.append(member_item)
            else:
                _new_members.append(member_item)

        # Set missing members
        old_member_ids = {member.character_id for member in _old_members}
        missing_members_ids = _current_members_ids - old_member_ids

        if missing_members_ids:
            self.filter(owner=owner, character_id__in=missing_members_ids).update(
                status=self.model.States.MISSING
            )
            logger.debug(
                "Marked %s missing members for: %s",
                len(missing_members_ids),
                owner.name,
            )
        if _old_members:
            self.bulk_update(
                _old_members,
                ["character_name", "status", "logon", "logged_off"],
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
            )
            logger.debug(
                "Updated %s members for: %s",
                len(_old_members),
                owner.name,
            )
        if _new_members:
            self.bulk_create(
                _new_members,
                batch_size=TAXSYSTEM_BULK_BATCH_SIZE,
                ignore_conflicts=True,
            )
            logger.debug(
                "Added %s new members for: %s",
                len(_new_members),
                owner.name,
            )

        # Update Members
        self._update_members(owner, _esi_members_ids)

        logger.info(
            "%s - Old Members: %s, New Members: %s, Missing: %s",
            owner.name,
            len(_old_members),
            len(_new_members),
            len(missing_members_ids),
        )
        return (
            "Finished members update for %s",
            owner.name,
        )

    def _update_members(self, owner: "OwnerContext", members_ids: list[int]):
        """Update Members for a corporation."""

        auth_accounts = UserProfile.objects.filter(
            main_character__isnull=False,
            main_character__corporation_id=owner.eve_corporation.corporation_id,
        ).prefetch_related("user__profile__main_character")

        members = self.filter(owner=owner)

        if not auth_accounts:
            logger.debug("No valid accounts for: %s", owner.name)
            return "No Accounts"

        for account in auth_accounts:
            # Get all alts for the user
            alts = set(
                account.user.character_ownerships.all().values_list(
                    "character__character_id", flat=True
                )
            )
            main = account.main_character

            # Change the status of members if they are alts
            relevant_alts = alts.intersection(members_ids)
            for alt in relevant_alts:
                members_ids.remove(alt)
                if alt == main.character_id:
                    # Update main character to active if it was previously in another state
                    members.filter(character_id=main.character_id).exclude(
                        status=self.model.States.ACTIVE
                    ).update(status=self.model.States.ACTIVE)
                else:
                    # Update the status of the member to alt
                    members.filter(character_id=alt).update(
                        status=self.model.States.IS_ALT
                    )

        if members_ids:
            # Mark members without accounts
            for member_id in members_ids:
                members.filter(character_id=member_id).update(
                    status=self.model.States.NOACCOUNT
                )

            logger.debug(
                "Marked %s members without accounts for: %s",
                len(members_ids),
                owner.name,
            )
        return "Updated Members statuses for %s", owner.name

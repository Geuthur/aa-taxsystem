"""Manager of `General` for the app's own permission rules."""

# Standard Library
from typing import Literal

# Django
from django.apps import apps
from django.db import models


class GeneralManager(models.Manager):
    """
    Manager of `General` for the app's own permission rules.

    Django checks single permissions (`user.has_perm("taxsystem.basic_access")`).
    This manager only holds the rules that combine them. `General` is not
    managed, so these methods never query `General`.
    """

    @staticmethod
    def has_management_access(user) -> bool:
        """
        Check if the user may use the Administration area.

        Requires at least one of admin_access, manage_corps, manage_own_corp,
        manage_alliances or manage_own_alliance (superusers pass implicitly).
        """
        return any(
            user.has_perm(f"taxsystem.{codename}")
            for codename in (
                "admin_access",
                "manage_corps",
                "manage_own_corp",
                "manage_alliances",
                "manage_own_alliance",
            )
        )

    @staticmethod
    def has_all_access(owner_type: Literal["corporation", "alliance"], user) -> bool:
        """
        Check if the user may administer ALL owners of the given type.

        Corporation: admin_access or manage_corps.
        Alliance: admin_access or manage_alliances.
        """
        if owner_type == "corporation":
            return user.has_perm("taxsystem.admin_access") or user.has_perm(
                "taxsystem.manage_corps"
            )
        if owner_type == "alliance":
            return user.has_perm("taxsystem.admin_access") or user.has_perm(
                "taxsystem.manage_alliances"
            )
        return False

    def get_administration_owners(
        self, owner_type: Literal["corporation", "alliance"], user
    ) -> models.QuerySet:
        """
        Return the owners of the given type the user may administer.

        All owners with the "all" permissions, otherwise only the own
        corporation/alliance (manage_own_corp / manage_own_alliance).
        """
        if owner_type not in ("corporation", "alliance"):
            raise ValueError(f"Invalid owner type: {owner_type}")

        # Resolved lazily to avoid circular imports with the owner models
        owner_model = apps.get_model(
            "taxsystem",
            "CorporationOwner" if owner_type == "corporation" else "AllianceOwner",
        )

        if self.has_all_access(owner_type, user):
            return owner_model.objects.all()
        # manage_to returns only the own owner for the manage_own_* permissions
        return owner_model.objects.manage_to(user)

    def has_administration_owner_access(
        self, owner_type: Literal["corporation", "alliance"], user, owner
    ) -> bool:
        """Check if the user may administer the given owner."""
        if not self.has_management_access(user):
            return False
        if owner_type not in ("corporation", "alliance"):
            return False
        return (
            self.get_administration_owners(owner_type, user)
            .filter(pk=owner.pk)
            .exists()
        )

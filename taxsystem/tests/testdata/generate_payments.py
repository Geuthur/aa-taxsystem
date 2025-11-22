# AA Tax System
# AA TaxSystem
from taxsystem.models.alliance import (
    AlliancePaymentAccount,
    AlliancePayments,
    AllianceUpdateStatus,
)
from taxsystem.models.corporation import (
    CorporationPaymentAccount,
    CorporationPayments,
    CorporationUpdateStatus,
    Members,
)


def create_payment(account: CorporationPaymentAccount, **kwargs) -> CorporationPayments:
    """Create a Payment for a Corporation"""
    params = {
        "account": account,
    }
    params.update(kwargs)
    payment = CorporationPayments(**params)
    payment.save()
    return payment


def create_member(owner: CorporationUpdateStatus, **kwargs) -> Members:
    """Create a Payment System for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    member = Members(**params)
    member.save()
    return member


def create_payment_system(
    owner: CorporationUpdateStatus, **kwargs
) -> CorporationPaymentAccount:
    """Create a Payment System for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    payment_system = CorporationPaymentAccount(**params)
    payment_system.save()
    return payment_system


def create_alliance_payment(
    account: AlliancePaymentAccount, **kwargs
) -> AlliancePayments:
    """Create a Payment for an Alliance"""
    params = {
        "account": account,
    }
    params.update(kwargs)
    payment = AlliancePayments(**params)
    payment.save()
    return payment


def create_alliance_payment_system(
    owner: AllianceUpdateStatus, **kwargs
) -> AlliancePaymentAccount:
    """Create a Payment System for an Alliance"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    payment_system = AlliancePaymentAccount(**params)
    payment_system.save()
    return payment_system

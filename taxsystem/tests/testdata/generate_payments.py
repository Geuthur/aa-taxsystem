# AA Tax System
# AA TaxSystem
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
    """Create a Member for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    member = Members(**params)
    member.save()
    return member


def create_tax_account(
    owner: CorporationUpdateStatus, **kwargs
) -> CorporationPaymentAccount:
    """Create a Tax Account for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    tax_account = CorporationPaymentAccount(**params)
    tax_account.save()
    return tax_account

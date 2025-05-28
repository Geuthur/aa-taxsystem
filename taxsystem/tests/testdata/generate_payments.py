# AA Tax System
# AA TaxSystem
from taxsystem.models.tax import Members, OwnerAudit, Payments, PaymentSystem


def create_payment(account: PaymentSystem, **kwargs) -> Payments:
    """Create a Payment for a Corporation"""
    params = {
        "account": account,
    }
    params.update(kwargs)
    payment = Payments(**params)
    payment.save()
    return payment


def create_member(owner: OwnerAudit, **kwargs) -> Members:
    """Create a Payment System for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    member = Members(**params)
    member.save()
    return member


def create_payment_system(owner: OwnerAudit, **kwargs) -> PaymentSystem:
    """Create a Payment System for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    payment_system = PaymentSystem(**params)
    payment_system.save()
    return payment_system

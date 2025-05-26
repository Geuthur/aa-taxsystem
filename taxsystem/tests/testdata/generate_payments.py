# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA TaxSystem
# AA Tax System
from taxsystem.models.tax import OwnerAudit, Payments, PaymentSystem


def create_payment(account: PaymentSystem, **kwargs) -> Payments:
    """Create a Payment for a Corporation"""
    params = {
        "account": account,
    }
    params.update(kwargs)
    payment = Payments(**params)
    payment.save()
    return payment


def create_payment_system(owner: OwnerAudit, **kwargs) -> PaymentSystem:
    """Create a Payment System for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    payment_system = PaymentSystem(**params)
    payment_system.save()
    return payment_system

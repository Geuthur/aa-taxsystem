# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import (
    create_user_from_evecharacter,
)

# AA TaxSystem
# AA Tax System
from taxsystem.models.tax import OwnerAudit
from taxsystem.models.wallet import (
    CorporationWalletDivision,
    CorporationWalletJournalEntry,
)


def create_division(corporation: OwnerAudit, **kwargs) -> CorporationWalletDivision:
    """Create a CorporationWalletDivision"""
    params = {
        "corporation": corporation,
    }
    params.update(kwargs)
    division = CorporationWalletDivision(**params)
    division.save()
    return division


def create_wallet_journal_entry(**kwargs) -> CorporationWalletJournalEntry:
    """Create a CorporationWalletJournalEntry"""
    params = {}
    params.update(kwargs)
    journal_entry = CorporationWalletJournalEntry(**params)
    journal_entry.save()
    return journal_entry

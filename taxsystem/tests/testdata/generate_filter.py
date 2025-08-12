# AA Tax System
# AA TaxSystem
from taxsystem.models.filters import JournalFilter, JournalFilterSet
from taxsystem.models.tax import OwnerAudit


def create_filterset(owner: OwnerAudit, **kwargs) -> JournalFilterSet:
    """Create a FilterSet for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    journal_filter_set = JournalFilterSet(**params)
    journal_filter_set.save()
    return journal_filter_set


def create_filter(filter_set: JournalFilterSet, **kwargs) -> JournalFilter:
    """Create a Filter for a Corporation"""
    params = {
        "filter_set": filter_set,
    }
    params.update(kwargs)
    journal_filter = JournalFilter(**params)
    journal_filter.save()
    return journal_filter

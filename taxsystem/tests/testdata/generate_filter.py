# AA Tax System
# AA TaxSystem
from taxsystem.models.alliance import (
    AllianceFilter,
    AllianceFilterSet,
    AllianceUpdateStatus,
)
from taxsystem.models.corporation import (
    CorporationFilter,
    CorporationFilterSet,
    CorporationUpdateStatus,
)


def create_filterset(owner: CorporationUpdateStatus, **kwargs) -> CorporationFilterSet:
    """Create a FilterSet for a Corporation"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    journal_filter_set = CorporationFilterSet(**params)
    journal_filter_set.save()
    return journal_filter_set


def create_filter(filter_set: CorporationFilterSet, **kwargs) -> CorporationFilter:
    """Create a Filter for a Corporation"""
    params = {
        "filter_set": filter_set,
    }
    params.update(kwargs)
    journal_filter = CorporationFilter(**params)
    journal_filter.save()
    return journal_filter


def create_alliance_filterset(
    owner: AllianceUpdateStatus, **kwargs
) -> AllianceFilterSet:
    """Create a FilterSet for an Alliance"""
    params = {
        "owner": owner,
    }
    params.update(kwargs)
    journal_filter_set = AllianceFilterSet(**params)
    journal_filter_set.save()
    return journal_filter_set


def create_alliance_filter(filter_set: AllianceFilterSet, **kwargs) -> AllianceFilter:
    """Create a Filter for an Alliance"""
    params = {
        "filter_set": filter_set,
    }
    params.update(kwargs)
    journal_filter = AllianceFilter(**params)
    journal_filter.save()
    return journal_filter

"""Initialize the app"""

__version__ = "2.0.2"
__title__ = "Tax System"

__package_name__ = "aa-taxsystem"
__app_name__ = "taxsystem"
__esi_compatibility_date__ = "2025-12-16"
__app_name_useragent__ = "AA-TaxSystem"

__github_url__ = f"https://github.com/Geuthur/{__package_name__}"

__operations__ = [
    "GetCorporationsCorporationIdWallets",
    "GetCorporationsCorporationIdWalletsDivisionJournal",
    "GetCorporationsCorporationIdDivisions",
    "GetCorporationsCorporationIdMembertracking",
    # Character operations
    "GetCharactersCharacterIdRoles",
    # Universe operations
    "PostUniverseNames",
]

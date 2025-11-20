"""Initialize the app"""

__version__ = "1.0.2"
__title__ = "Tax System"

__package_name__ = "aa-taxsystem"
__app_name__ = "taxsystem"
__esi_compatibility_date__ = "2025-11-06"
__app_name_useragent__ = "AA-TaxSystem"

__github_url__ = f"https://github.com/Geuthur/{__package_name__}"

__corporation_operations__ = [
    "GetCorporationsCorporationIdWallets",
    "GetCorporationsCorporationIdWalletsDivisionJournal",
    "GetCorporationsCorporationIdDivisions",
    "GetCorporationsCorporationIdMembertracking",
]

__character_operations__ = [
    "GetCharactersCharacterIdRoles",
]

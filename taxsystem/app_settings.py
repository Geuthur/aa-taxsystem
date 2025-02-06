"""
App Settings
"""

import sys

# Django
from app_utils.app_settings import clean_setting

IS_TESTING = sys.argv[1:2] == ["test"]

# EVE Online Swagger
EVE_BASE_URL = "https://esi.evetech.net/"
EVE_API_URL = "https://esi.evetech.net/latest/"
EVE_BASE_URL_REGEX = r"^http[s]?:\/\/esi.evetech\.net\/"

# Fuzzwork
FUZZ_BASE_URL = "https://www.fuzzwork.co.uk/"
FUZZ_API_URL = "https://www.fuzzwork.co.uk/api/"
FUZZ_BASE_URL_REGEX = r"^http[s]?:\/\/(www\.)?fuzzwork\.co\.uk\/"

# ZKillboard
ZKILLBOARD_BASE_URL = "https://zkillboard.com/"
ZKILLBOARD_API_URL = "https://zkillboard.com/api/"
ZKILLBOARD_BASE_URL_REGEX = r"^http[s]?:\/\/zkillboard\.com\/"
ZKILLBOARD_KILLMAIL_URL_REGEX = r"^http[s]?:\/\/zkillboard\.com\/kill\/\d+\/"

# Set Test Mode True or False

# Set Naming on Auth Hook
TAXSYSTEM_APP_NAME = clean_setting("TAXSYSTEM_APP_NAME", "Tax System")

# If True you need to set up the Logger
TAXSYSTEM_LOGGER_USE = clean_setting("TAXSYSTEM_LOGGER_USE", False)

# Skip Dates for Audit

# Member Skip Date in Days
TAXSYSTEM_CORP_MEMBERS_SKIP_DATE = clean_setting("TAXSYSTEM_CORP_MEMBERS_SKIP_DATE", 1)
# Wallet Skip Date in Hours
TAXSYSTEM_CORP_WALLET_SKIP_DATE = clean_setting("TAXSYSTEM_CORP_WALLET_SKIP_DATE", 1)
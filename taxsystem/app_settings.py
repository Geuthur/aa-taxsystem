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

# Set Naming on Auth Hook
TAXSYSTEM_APP_NAME = clean_setting("TAXSYSTEM_APP_NAME", "Tax System")

# If True you need to set up the Logger
TAXSYSTEM_LOGGER_USE = clean_setting("TAXSYSTEM_LOGGER_USE", False)

# Task Settings
# Global timeout for tasks in seconds to reduce task accumulation during outages.
TAXSYSTEM_TASKS_TIME_LIMIT = clean_setting("TAXSYSTEM_TASKS_TIME_LIMIT", 7200)

# Stale Time
TAXSYSTEM_STALE_TIME = clean_setting("TAXSYSTEM_STALE_TIME", 3)

# Skip Dates for Tasks
# Member Skip Date in Hours
TAXSYSTEM_CORP_MEMBERS_SKIP_DATE = clean_setting("TAXSYSTEM_CORP_MEMBERS_SKIP_DATE", 1)
# Wallet Skip Date in Hours
TAXSYSTEM_CORP_WALLET_SKIP_DATE = clean_setting("TAXSYSTEM_CORP_WALLET_SKIP_DATE", 1)
# Payment Skip Date in Hours
TAXSYSTEM_CORP_PAYMENTS_SKIP_DATE = clean_setting(
    "TAXSYSTEM_CORP_PAYMENTS_SKIP_DATE", 1
)
# Filter Skip Date in Hours
TAXSYSTEM_CORP_PAYMENT_SYSTEM_SKIP_DATE = clean_setting(
    "TAXSYSTEM_CORP_PAYMENT_SYSTEM_SKIP_DATE", 1
)
# Payment Payday Skip Date in Hours
TAXSYSTEM_CORP_PAYMENT_PAYDAY_SKIP_DATE = clean_setting(
    "TAXSYSTEM_CORP_PAYMENT_PAYDAY_SKIP_DATE", 24
)

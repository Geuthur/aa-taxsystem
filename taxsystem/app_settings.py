"""
App Settings
"""

# Standard Library
import sys

# Alliance Auth (External Libs)
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

# Task Settings
# Global timeout for tasks in seconds to reduce task accumulation during outages.
TAXSYSTEM_TASKS_TIME_LIMIT = clean_setting("TAXSYSTEM_TASKS_TIME_LIMIT", 7200)

# Stale time in minutes for each type of data
TAXSYSTEM_STALE_TYPES = {
    "wallet": 60,
    "division_names": 60,
    "division": 15,
    "members": 60,
    "payments": 60,
    "payment_system": 60,
    "payment_payday": 1440,
}

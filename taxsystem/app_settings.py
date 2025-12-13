"""
App Settings
"""

# Django
from django.conf import settings

# Set Naming on Auth Hook
TAXSYSTEM_APP_NAME = getattr(settings, "TAXSYSTEM_APP_NAME", "Tax System")

# Task Settings
# Global timeout for tasks in seconds to reduce task accumulation during outages.
TAXSYSTEM_TASKS_TIME_LIMIT = getattr(settings, "TAXSYSTEM_TASKS_TIME_LIMIT", 7200)

# Stale time in minutes for each type of data
TAXSYSTEM_STALE_TYPES = {
    "wallet": 60,
    "division_names": 60,
    "division": 30,
    "members": 60,
    "payments": 60,
    "payment_system": 60,
    "payment_payday": 1440,
}

# Controls how many database records are inserted in a single batch operation.
TAXSYSTEM_BULK_BATCH_SIZE = getattr(settings, "TAXSYSTEM_BULK_BATCH_SIZE", 500)

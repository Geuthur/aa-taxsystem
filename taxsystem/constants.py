"""
Constants
"""

# Standard Library
import os

AA_TAXSYSTEM_BASE_DIR = os.path.join(os.path.dirname(__file__))
AA_TAXSYSTEM_STATIC_DIR = os.path.join(AA_TAXSYSTEM_BASE_DIR, "static", "taxsystem")

# Common select_related fields for UserProfile / main_character joins
AUTH_SELECT_RELATED_MAIN_CHARACTER = (
    "user__profile__main_character",
    "main_character__character_ownership",
    "main_character__character_ownership__user__profile",
    "main_character__character_ownership__user__profile__main_character",
)

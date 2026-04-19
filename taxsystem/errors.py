"""Custom exceptions."""


class DatabaseError(Exception):
    """Custom exception to indicate a database error."""


class DownTimeError(Exception):
    """Custom exception to indicate ESI is in daily downtime."""

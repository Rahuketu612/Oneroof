"""
OneRoof Core Module
Contains configuration, database, and security components.
"""

from oneroof.core.config import settings, get_settings
from oneroof.core.database import Base, engine, get_db
from oneroof.core.security import (
    SecurityMiddleware,
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
)

__all__ = [
    "settings",
    "get_settings",
    "Base",
    "engine",
    "get_db",
    "SecurityMiddleware",
    "get_current_user",
    "get_password_hash",
    "verify_password",
    "create_access_token",
]
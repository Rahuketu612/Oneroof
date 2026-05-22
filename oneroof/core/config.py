"""
Configuration settings for OneRoof application.
All configuration loaded from environment variables.
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    APP_NAME: str = "OneRoof"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://oneroof:password@localhost:5432/oneroof"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # File Storage
    UPLOAD_DIR: str = "/var/oneroof/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".xlsx", ".xls", ".docx", ".doc", ".jpg", ".png"]

    # Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"
    
    # Redis (for caching and task queue)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email (for notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Compliance Defaults
    GST_REMINDER_DAYS: List[int] = [-5, -2, 0]  # Days before/after deadline
    TDS_REMINDER_DAYS: List[int] = [-7, -3, 0]
    
    # Audit
    AUDIT_RETENTION_DAYS: int = 2555  # ~7 years for compliance

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
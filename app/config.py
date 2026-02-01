"""
Application configuration for different environments.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_database_url():
    """Get database URL, converting postgres:// to postgresql:// for SQLAlchemy."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    ITEMS_PER_PAGE = 20
    
    # Store info for receipts
    STORE_NAME = os.environ.get("STORE_NAME", "Grocery Store")
    STORE_ADDRESS = os.environ.get("STORE_ADDRESS", "123 Main St")
    STORE_PHONE = os.environ.get("STORE_PHONE", "+1 234 567 8900")
    TAX_RATE = float(os.environ.get("TAX_RATE", "0.08"))

    # PostgreSQL connection settings (for local development)
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "grocery_store")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = "development"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Use DATABASE_URL if set, otherwise construct from individual settings
        return get_database_url() or (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return get_database_url() or (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}_test"
        )


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = "production"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Production MUST use DATABASE_URL from Render
        url = get_database_url()
        if not url:
            raise ValueError("DATABASE_URL environment variable is required in production")
        return url

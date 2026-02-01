"""
Application configuration for different environments.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


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

    # PostgreSQL connection settings
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "grocery_store")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = "development"
    # Use DATABASE_URL if set, otherwise construct PostgreSQL URL from individual settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
        f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # Use PostgreSQL for testing as well (can use a separate test database)
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL") or (
        f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
        f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}_test"
    )
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = "production"
    # Production must use DATABASE_URL environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or ""

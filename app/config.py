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


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = "development"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or f"sqlite:///{BASE_DIR / 'instance' / 'grocery.db'}"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = "production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or ""

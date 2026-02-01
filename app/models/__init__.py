"""
Database models - import all so they are registered with SQLAlchemy.
"""
from app import db
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.customer import Customer
from app.models.sale import Sale, SaleItem
from app.models.activity_log import ActivityLog
from app.models.shift import Shift
from app.models.promotion import Promotion

__all__ = [
    "User",
    "Category",
    "Supplier",
    "Product",
    "Customer",
    "Sale",
    "SaleItem",
    "ActivityLog",
    "Shift",
    "Promotion",
]

"""
Product model for inventory (name, category, price, quantity, expiration, supplier, barcode/SKU).
"""
from datetime import datetime, date
from decimal import Decimal
from app import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit = db.Column(db.String(20), nullable=True, default="pcs")  # pcs, kg, L, etc.
    expiration_date = db.Column(db.Date, nullable=True)
    sku = db.Column(db.String(60), unique=True, nullable=True, index=True)
    barcode = db.Column(db.String(60), unique=True, nullable=True, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    min_stock = db.Column(db.Integer, nullable=False, default=0)  # alert when quantity <= this
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale_items = db.relationship("SaleItem", backref="product", lazy="dynamic")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.min_stock

    @property
    def is_expired_or_near(self, days_near: int = 7) -> bool:
        if not self.expiration_date:
            return False
        today = date.today()
        return self.expiration_date <= today or (self.expiration_date - today).days <= days_near

    def __repr__(self):
        return f"<Product {self.name} ({self.sku})>"

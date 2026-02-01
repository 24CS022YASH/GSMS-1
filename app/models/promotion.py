"""
Promotion for discounts (percentage or fixed) and special offers.
"""
from datetime import datetime, date
from decimal import Decimal
from app import db


class Promotion(db.Model):
    __tablename__ = "promotions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    promo_type = db.Column(db.String(20), nullable=False)  # percentage, fixed
    value = db.Column(db.Numeric(12, 2), nullable=False)  # e.g. 10 for 10%, or 5.00 for $5 off
    min_purchase = db.Column(db.Numeric(12, 2), nullable=True)  # minimum cart total to apply
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_to = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid_now(self) -> bool:
        if not self.active:
            return False
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def __repr__(self):
        return f"<Promotion {self.name}>"

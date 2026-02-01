"""
Customer model for optional registration, loyalty, and purchase history.
"""
from datetime import datetime
from app import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    loyalty_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales = db.relationship("Sale", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer {self.name}>"

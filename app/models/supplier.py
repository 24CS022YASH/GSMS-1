"""
Supplier model for product sourcing.
"""
from app import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    contact_person = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    products = db.relationship("Product", backref="supplier", lazy="dynamic")

    def __repr__(self):
        return f"<Supplier {self.name}>"

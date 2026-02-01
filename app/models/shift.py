"""
Shift and register balancing for cashiers.
"""
from datetime import datetime
from decimal import Decimal
from app import db


class Shift(db.Model):
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    register_id = db.Column(db.String(20), nullable=True)
    open_cash = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    close_cash = db.Column(db.Numeric(12, 2), nullable=True)
    start_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Shift user={self.user_id} {self.start_at}>"

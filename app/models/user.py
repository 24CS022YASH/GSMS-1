"""
User model for role-based access (admin, manager, cashier).
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="cashier")  # admin, manager, cashier
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sales = db.relationship("Sale", backref="user", lazy="dynamic", foreign_keys="Sale.user_id")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic")
    shifts = db.relationship("Shift", backref="user", lazy="dynamic")

    ROLES = ("admin", "manager", "cashier")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_manager_or_above(self) -> bool:
        return self.role in ("admin", "manager")

    def __repr__(self):
        return f"<User {self.username}>"

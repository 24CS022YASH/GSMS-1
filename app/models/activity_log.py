"""
Activity log for audit trail of system actions.
"""
from datetime import datetime
from app import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, etc.
    entity_type = db.Column(db.String(50), nullable=True)  # product, sale, user, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog {self.action} {self.entity_type}:{self.entity_id}>"

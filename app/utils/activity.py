"""
Activity logging for audit trail.
"""
from flask import request
from app import db
from app.models.activity_log import ActivityLog


def log_activity(action: str, entity_type: str = None, entity_id: int = None, details: str = None):
    """Log an activity for the current user."""
    user_id = None
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            user_id = current_user.id
    except Exception:
        pass
    ip = request.remote_addr if request else None
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip,
    )
    db.session.add(log)
    # Caller should commit; avoid committing here to stay in same transaction

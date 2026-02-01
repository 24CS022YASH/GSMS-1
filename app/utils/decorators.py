"""
Role-based access control decorators.
"""
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def login_required(f):
    """Require user to be logged in (Flask-Login provides this; we add flash)."""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.active:
            flash("Your account is disabled.", "danger")
            return redirect(url_for("auth.logout"))
        return f(*args, **kwargs)
    return decorated_view


def role_required(*roles):
    """Require current user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorated_view
    return decorator


def admin_required(f):
    return role_required("admin")(f)


def manager_required(f):
    return role_required("admin", "manager")(f)

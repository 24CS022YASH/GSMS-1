"""
User management: CRUD, roles, activity log, shift balancing.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.shift import Shift
from app.utils.decorators import login_required, admin_required
from app.utils.activity import log_activity

users_bp = Blueprint("users", __name__)


@users_bp.route("/")
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.username).all()
    return render_template("users/list.html", users=users)


@users_bp.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def user_add():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password")
        role = (request.form.get("role") or "cashier").strip()
        full_name = (request.form.get("full_name") or "").strip() or None
        email = (request.form.get("email") or "").strip() or None
        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("users.user_add"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("users.user_add"))
        if not password or len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
            return redirect(url_for("users.user_add"))
        if role not in User.ROLES:
            role = "cashier"
        user = User(username=username, role=role, full_name=full_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_activity("create", "user", user.id, f"User {username}")
        flash("User created.", "success")
        return redirect(url_for("users.user_list"))
    return render_template("users/form.html", user=None)


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("users.user_list"))
    if request.method == "POST":
        user.role = (request.form.get("role") or user.role).strip()
        if user.role not in User.ROLES:
            user.role = "cashier"
        user.full_name = (request.form.get("full_name") or "").strip() or None
        user.email = (request.form.get("email") or "").strip() or None
        user.active = request.form.get("active") == "1"
        password = request.form.get("password")
        if password:
            user.set_password(password)
        db.session.commit()
        log_activity("update", "user", user.id, user.username)
        flash("User updated.", "success")
        return redirect(url_for("users.user_list"))
    return render_template("users/form.html", user=user)


@users_bp.route("/activity")
@login_required
@admin_required
def activity_log():
    page = request.args.get("page", 1, type=int)
    pagination = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("users/activity_log.html", pagination=pagination)


@users_bp.route("/shifts")
@login_required
@admin_required
def shift_list():
    shifts = Shift.query.order_by(Shift.start_at.desc()).limit(100).all()
    return render_template("users/shifts.html", shifts=shifts)


@users_bp.route("/shifts/start", methods=["GET", "POST"])
@login_required
def shift_start():
    if request.method == "POST":
        open_cash = request.form.get("open_cash") or "0"
        register_id = (request.form.get("register_id") or "").strip() or None
        try:
            open_cash = float(open_cash)
        except ValueError:
            open_cash = 0
        shift = Shift(user_id=current_user.id, register_id=register_id, open_cash=open_cash)
        db.session.add(shift)
        db.session.commit()
        log_activity("shift_start", "shift", shift.id, f"Register {register_id}")
        flash("Shift started.", "success")
        return redirect(url_for("users.shift_list"))
    return render_template("users/shift_form.html", shift=None)


@users_bp.route("/shifts/<int:shift_id>/end", methods=["GET", "POST"])
@login_required
def shift_end(shift_id):
    shift = Shift.query.get(shift_id)
    if not shift or shift.user_id != current_user.id:
        flash("Shift not found or not yours.", "danger")
        return redirect(url_for("users.shift_list"))
    if shift.end_at:
        flash("Shift already ended.", "info")
        return redirect(url_for("users.shift_list"))
    if request.method == "POST":
        close_cash = request.form.get("close_cash") or "0"
        try:
            close_cash = float(close_cash)
        except ValueError:
            close_cash = 0
        from datetime import datetime
        shift.close_cash = close_cash
        shift.end_at = datetime.utcnow()
        db.session.commit()
        log_activity("shift_end", "shift", shift.id, f"Close cash {close_cash}")
        flash("Shift ended.", "success")
        return redirect(url_for("users.shift_list"))
    return render_template("users/shift_end.html", shift=shift)

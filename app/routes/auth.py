"""
Authentication: login, logout, profile.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.utils.activity import log_activity

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html")
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")
        if not user.active:
            flash("Your account is disabled.", "danger")
            return render_template("auth/login.html")
        login_user(user)
        log_activity("login", "user", user.id, "User logged in")
        db.session.commit()
        next_page = request.args.get("next") or url_for("main.dashboard")
        return redirect(next_page)
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    uid = current_user.id
    logout_user()
    log_activity("logout", "user", uid, "User logged out")
    db.session.commit()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")

"""
Main dashboard and home routes.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.utils.decorators import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

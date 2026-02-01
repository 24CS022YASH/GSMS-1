"""
Analytics and reporting: sales reports, inventory, exports.
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, send_file, jsonify
from flask_login import current_user
from app.utils.decorators import login_required, manager_required
from app.services import report_service as reports
from app.config import Config
import io

analytics_bp = Blueprint("analytics", __name__)


def parse_dates():
    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
        except ValueError:
            start_date = date.today() - timedelta(days=30)
    else:
        start_date = date.today() - timedelta(days=30)
    if end:
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            end_date = date.today()
    else:
        end_date = date.today()
    return start_date, end_date


@analytics_bp.route("/")
@login_required
@manager_required
def dashboard():
    start_date, end_date = parse_dates()
    summary = reports.sales_summary(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
    )
    daily = reports.sales_report(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
    )
    best = reports.best_selling_products(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
        limit=10,
    )
    return render_template(
        "analytics/dashboard.html",
        summary=summary,
        daily=daily,
        best_selling=best,
        start_date=start_date,
        end_date=end_date,
    )


@analytics_bp.route("/sales")
@login_required
@manager_required
def sales_report_page():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    summary = reports.sales_summary(start_dt, end_dt)
    daily = reports.sales_report(start_dt, end_dt)
    return render_template(
        "analytics/sales_report.html",
        summary=summary,
        daily=daily,
        start_date=start_date,
        end_date=end_date,
    )


@analytics_bp.route("/inventory")
@login_required
@manager_required
def inventory_report():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    turnover = reports.inventory_turnover(start_dt, end_dt)
    slow = reports.slow_moving_products(limit=15)
    best = reports.best_selling_products(start_dt, end_dt, limit=15)
    return render_template(
        "analytics/inventory_report.html",
        turnover=turnover,
        slow_moving=slow,
        best_selling=best,
        start_date=start_date,
        end_date=end_date,
    )


@analytics_bp.route("/export/csv")
@login_required
@manager_required
def export_csv():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    lines = reports.export_sales_csv(start_dt, end_dt)
    buf = io.BytesIO()
    for line in lines:
        buf.write(line.encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"sales_{start_date}_{end_date}.csv",
    )


@analytics_bp.route("/export/excel")
@login_required
@manager_required
def export_excel():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    bio = reports.export_sales_excel_io(start_dt, end_dt)
    if not bio:
        return "Excel export not available", 500
    return send_file(
        bio,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"sales_{start_date}_{end_date}.xlsx",
    )


@analytics_bp.route("/export/pdf")
@login_required
@manager_required
def export_pdf():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    store_name = getattr(Config, "STORE_NAME", "Grocery Store")
    bio = reports.export_sales_pdf_io(start_dt, end_dt, store_name=store_name)
    if not bio:
        return "PDF export not available", 500
    return send_file(
        bio,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"sales_{start_date}_{end_date}.pdf",
    )


@analytics_bp.route("/api/chart")
@login_required
@manager_required
def api_chart():
    start_date, end_date = parse_dates()
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    daily = reports.sales_report(start_dt, end_dt)
    return jsonify({"labels": [r["period"] for r in daily], "data": [r["total_sales"] for r in daily]})

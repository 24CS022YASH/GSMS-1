"""
Customer management: CRUD, purchase history, loyalty.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from app import db
from sqlalchemy import or_
from app.models.customer import Customer
from app.models.sale import Sale
from app.utils.decorators import login_required, manager_required
from app.utils.activity import log_activity

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("/")
@login_required
@manager_required
def customer_list():
    search = (request.args.get("search") or "").strip() or None
    q = Customer.query
    if search:
        term = f"%{search}%"
        q = q.filter(or_(Customer.name.ilike(term), Customer.email.ilike(term), Customer.phone.ilike(term)))
    customers = q.order_by(Customer.name).limit(200).all()
    return render_template("customers/list.html", customers=customers, search=search)


@customers_bp.route("/add", methods=["GET", "POST"])
@login_required
@manager_required
def customer_add():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for("customers.customer_add"))
        c = Customer(
            name=name,
            email=(request.form.get("email") or "").strip() or None,
            phone=(request.form.get("phone") or "").strip() or None,
            loyalty_points=int(request.form.get("loyalty_points") or 0),
        )
        db.session.add(c)
        db.session.commit()
        log_activity("create", "customer", c.id, name)
        flash("Customer added.", "success")
        return redirect(url_for("customers.customer_list"))
    return render_template("customers/form.html", customer=None)


@customers_bp.route("/<int:customer_id>")
@login_required
@manager_required
def customer_detail(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("customers.customer_list"))
    sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.created_at.desc()).limit(50).all()
    return render_template("customers/detail.html", customer=customer, sales=sales)


@customers_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@manager_required
def customer_edit(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("customers.customer_list"))
    if request.method == "POST":
        customer.name = (request.form.get("name") or "").strip() or customer.name
        customer.email = (request.form.get("email") or "").strip() or None
        customer.phone = (request.form.get("phone") or "").strip() or None
        try:
            customer.loyalty_points = int(request.form.get("loyalty_points") or 0)
        except ValueError:
            pass
        db.session.commit()
        log_activity("update", "customer", customer.id, customer.name)
        flash("Customer updated.", "success")
        return redirect(url_for("customers.customer_detail", customer_id=customer_id))
    return render_template("customers/form.html", customer=customer)

"""
Inventory management: products, categories, suppliers, batch, alerts.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app import db
from app.utils.decorators import login_required, manager_required
from app.utils.activity import log_activity
from app.services import inventory_service as inv
from app.models.category import Category
from app.models.supplier import Supplier

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/")
@login_required
def product_list():
    page = request.args.get("page", 1, type=int)
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("search", "").strip() or None
    low_stock = request.args.get("low_stock", type=lambda x: x == "1")
    pagination = inv.get_products_paginated(
        page=page, category_id=category_id, search=search, low_stock_only=low_stock
    )
    categories = inv.get_categories_all()
    return render_template(
        "inventory/product_list.html",
        pagination=pagination,
        categories=categories,
        category_id=category_id,
        search=search,
        low_stock=low_stock,
    )


@inventory_bp.route("/product/add", methods=["GET", "POST"])
@login_required
@manager_required
def product_add():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("inventory.product_add"))
        price = request.form.get("price") or "0"
        quantity = request.form.get("quantity") or "0"
        category_id = request.form.get("category_id") or None
        if category_id is not None:
            try:
                category_id = int(category_id)
            except ValueError:
                category_id = None
        unit = (request.form.get("unit") or "pcs").strip()
        exp = request.form.get("expiration_date") or None
        if exp:
            try:
                from datetime import datetime
                exp = datetime.strptime(exp, "%Y-%m-%d").date()
            except ValueError:
                exp = None
        sku = (request.form.get("sku") or "").strip() or None
        barcode = (request.form.get("barcode") or "").strip() or None
        supplier_id = request.form.get("supplier_id") or None
        if supplier_id is not None:
            try:
                supplier_id = int(supplier_id)
            except ValueError:
                supplier_id = None
        min_stock = request.form.get("min_stock") or "0"
        product, err = inv.add_product(
            name=name, price=price, quantity=quantity, category_id=category_id,
            unit=unit, expiration_date=exp, sku=sku, barcode=barcode,
            supplier_id=supplier_id, min_stock=min_stock,
        )
        if err:
            flash(err, "danger")
            return redirect(url_for("inventory.product_add"))
        log_activity("create", "product", product.id, f"Added product {product.name}")
        db.session.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for("inventory.product_list"))
    categories = inv.get_categories_all()
    suppliers = inv.get_suppliers_all()
    return render_template("inventory/product_form.html", product=None, categories=categories, suppliers=suppliers)


@inventory_bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@manager_required
def product_edit(product_id):
    product = inv.get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("inventory.product_list"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Product name is required.", "danger")
            return redirect(url_for("inventory.product_edit", product_id=product_id))
        price = request.form.get("price") or "0"
        quantity = request.form.get("quantity") or "0"
        category_id = request.form.get("category_id") or None
        try:
            category_id = int(category_id) if category_id else None
        except ValueError:
            category_id = None
        unit = (request.form.get("unit") or "pcs").strip()
        exp = request.form.get("expiration_date") or None
        if exp:
            try:
                from datetime import datetime
                exp = datetime.strptime(exp, "%Y-%m-%d").date()
            except ValueError:
                exp = None
        sku = (request.form.get("sku") or "").strip() or None
        barcode = (request.form.get("barcode") or "").strip() or None
        supplier_id = request.form.get("supplier_id") or None
        try:
            supplier_id = int(supplier_id) if supplier_id else None
        except ValueError:
            supplier_id = None
        min_stock = request.form.get("min_stock") or "0"
        _, err = inv.update_product(
            product_id,
            name=name, price=price, quantity=quantity, category_id=category_id,
            unit=unit, expiration_date=exp, sku=sku, barcode=barcode,
            supplier_id=supplier_id, min_stock=min_stock,
        )
        if err:
            flash(err, "danger")
            return redirect(url_for("inventory.product_edit", product_id=product_id))
        log_activity("update", "product", product_id, f"Updated product {name}")
        db.session.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for("inventory.product_list"))
    categories = inv.get_categories_all()
    suppliers = inv.get_suppliers_all()
    return render_template("inventory/product_form.html", product=product, categories=categories, suppliers=suppliers)


@inventory_bp.route("/product/<int:product_id>/delete", methods=["POST"])
@login_required
@manager_required
def product_delete(product_id):
    ok, err = inv.delete_product(product_id)
    if not ok:
        flash(err or "Delete failed.", "danger")
        return redirect(url_for("inventory.product_list"))
    log_activity("delete", "product", product_id, "Product deleted")
    db.session.commit()
    flash("Product removed.", "success")
    return redirect(url_for("inventory.product_list"))


@inventory_bp.route("/batch", methods=["GET", "POST"])
@login_required
@manager_required
def batch_update():
    if request.method == "POST":
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"success": False, "error": "Expected JSON array"}), 400
        success, errors = inv.batch_update_products(data)
        log_activity("batch_update", "product", None, f"Batch updated {success} products")
        db.session.commit()
        return jsonify({"success": True, "updated": success, "errors": errors})
    return render_template("inventory/batch_update.html")


@inventory_bp.route("/alerts")
@login_required
def alerts():
    low_stock = inv.get_low_stock_products()
    expired_near = inv.get_expired_or_near_products(days_near=7)
    return render_template("inventory/alerts.html", low_stock=low_stock, expired_near=expired_near)


# Categories CRUD (simple)
@inventory_bp.route("/categories")
@login_required
@manager_required
def category_list():
    categories = inv.get_categories_all()
    return render_template("inventory/category_list.html", categories=categories)


@inventory_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
@manager_required
def category_add():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        desc = (request.form.get("description") or "").strip() or None
        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("inventory.category_add"))
        if Category.query.filter_by(name=name).first():
            flash("Category already exists.", "danger")
            return redirect(url_for("inventory.category_add"))
        c = Category(name=name, description=desc)
        db.session.add(c)
        db.session.commit()
        log_activity("create", "category", c.id, f"Category {name}")
        flash("Category added.", "success")
        return redirect(url_for("inventory.category_list"))
    return render_template("inventory/category_form.html", category=None)


@inventory_bp.route("/categories/<int:cat_id>/edit", methods=["GET", "POST"])
@login_required
@manager_required
def category_edit(cat_id):
    c = Category.query.get(cat_id)
    if not c:
        flash("Category not found.", "danger")
        return redirect(url_for("inventory.category_list"))
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Name is required.", "danger")
            return redirect(url_for("inventory.category_edit", cat_id=cat_id))
        c.name = name
        c.description = (request.form.get("description") or "").strip() or None
        db.session.commit()
        log_activity("update", "category", c.id, name)
        flash("Category updated.", "success")
        return redirect(url_for("inventory.category_list"))
    return render_template("inventory/category_form.html", category=c)


# Suppliers CRUD
@inventory_bp.route("/suppliers")
@login_required
@manager_required
def supplier_list():
    suppliers = inv.get_suppliers_all()
    return render_template("inventory/supplier_list.html", suppliers=suppliers)


@inventory_bp.route("/suppliers/add", methods=["GET", "POST"])
@login_required
@manager_required
def supplier_add():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Supplier name is required.", "danger")
            return redirect(url_for("inventory.supplier_add"))
        s = Supplier(
            name=name,
            contact_person=(request.form.get("contact_person") or "").strip() or None,
            email=(request.form.get("email") or "").strip() or None,
            phone=(request.form.get("phone") or "").strip() or None,
            address=(request.form.get("address") or "").strip() or None,
        )
        db.session.add(s)
        db.session.commit()
        log_activity("create", "supplier", s.id, name)
        flash("Supplier added.", "success")
        return redirect(url_for("inventory.supplier_list"))
    return render_template("inventory/supplier_form.html", supplier=None)


@inventory_bp.route("/suppliers/<int:sup_id>/edit", methods=["GET", "POST"])
@login_required
@manager_required
def supplier_edit(sup_id):
    s = Supplier.query.get(sup_id)
    if not s:
        flash("Supplier not found.", "danger")
        return redirect(url_for("inventory.supplier_list"))
    if request.method == "POST":
        s.name = (request.form.get("name") or "").strip() or s.name
        s.contact_person = (request.form.get("contact_person") or "").strip() or None
        s.email = (request.form.get("email") or "").strip() or None
        s.phone = (request.form.get("phone") or "").strip() or None
        s.address = (request.form.get("address") or "").strip() or None
        db.session.commit()
        log_activity("update", "supplier", s.id, s.name)
        flash("Supplier updated.", "success")
        return redirect(url_for("inventory.supplier_list"))
    return render_template("inventory/supplier_form.html", supplier=s)

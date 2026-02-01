"""
POS: cart, checkout, receipt, refund.
"""
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import current_user
from app import db
from app.utils.decorators import login_required, manager_required
from app.utils.activity import log_activity
from app.services.inventory_service import lookup_product
from app.services.billing_service import (
    calculate_cart_totals,
    create_sale,
    create_refund,
    get_active_promotions,
)
from app.models.sale import Sale
from app.config import Config

pos_bp = Blueprint("pos", __name__)

CART_KEY = "pos_cart"


def get_cart():
    return session.get(CART_KEY) or []


def set_cart(cart):
    session[CART_KEY] = cart


@pos_bp.route("/")
@login_required
def index():
    # If redirected from lookup with add_id, add that product to cart (add_qty from form)
    add_id = request.args.get("add_id", type=int)
    add_qty = request.args.get("add_qty", type=int) or 1
    if add_id:
        product = lookup_product(add_id)
        if product and product.quantity >= 1:
            qty = max(1, min(add_qty, product.quantity))
            cart = get_cart()
            existing = next((i for i in cart if i["product_id"] == product.id), None)
            price = float(product.price)
            if existing:
                new_qty = existing["quantity"] + qty
                if product.quantity < new_qty:
                    flash(f"Insufficient stock for {product.name} (have {product.quantity}).", "warning")
                    return redirect(url_for("pos.index"))
                existing["quantity"] = new_qty
                existing["subtotal"] = round(price * new_qty, 2)
            else:
                cart.append({
                    "product_id": product.id,
                    "name": product.name,
                    "price": price,
                    "quantity": qty,
                    "subtotal": round(price * qty, 2),
                })
            set_cart(cart)
            flash(f"Added {product.name} x{qty} to cart.", "success")
        else:
            flash("Product not found or out of stock.", "warning")
        return redirect(url_for("pos.index"))
    cart = get_cart()
    totals = calculate_cart_totals(cart) if cart else {}
    promotions = get_active_promotions()
    return render_template("pos/index.html", cart=cart, totals=totals, promotions=promotions)


@pos_bp.route("/lookup", methods=["GET", "POST"])
@login_required
def lookup():
    """Lookup product by id, sku, barcode, or product name (GET q= or POST identifier)."""
    identifier = request.args.get("q") or request.form.get("identifier")
    if request.is_json:
        identifier = identifier or request.json.get("identifier")
    if identifier is not None and isinstance(identifier, str):
        identifier = identifier.strip()
    if not identifier:
        if request.is_json:
            return jsonify({"success": False, "error": "Enter barcode, SKU, or product name"}), 400
        flash("Enter barcode, SKU, or product name to search.", "warning")
        return redirect(url_for("pos.index"))
    product = lookup_product(identifier)
    if not product:
        if request.is_json:
            return jsonify({"success": False, "error": "Product not found"}), 404
        flash("Product not found.", "warning")
        return redirect(url_for("pos.index"))
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "price": str(product.price),
                "quantity": product.quantity,
                "unit": product.unit or "pcs",
                "sku": product.sku,
                "barcode": product.barcode,
            },
        })
    add_qty = request.args.get("add_qty", type=int) or 1
    return redirect(url_for("pos.index", add_id=product.id, add_qty=add_qty))


@pos_bp.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    product_id = request.form.get("product_id") or request.json.get("product_id")
    quantity = request.form.get("quantity") or request.json.get("quantity") or 1
    if not product_id:
        if request.is_json:
            return jsonify({"success": False, "error": "product_id required"}), 400
        flash("Product required.", "warning")
        return redirect(url_for("pos.index"))
    product = lookup_product(product_id)
    if not product:
        if request.is_json:
            return jsonify({"success": False, "error": "Product not found"}), 404
        flash("Product not found.", "warning")
        return redirect(url_for("pos.index"))
    qty = int(quantity)
    if qty <= 0:
        qty = 1
    if product.quantity < qty:
        if request.is_json:
            return jsonify({"success": False, "error": f"Insufficient stock (have {product.quantity})"}), 400
        flash(f"Insufficient stock for {product.name}.", "warning")
        return redirect(url_for("pos.index"))
    price = float(product.price)
    subtotal = price * qty
    cart = get_cart()
    existing = next((i for i in cart if i["product_id"] == product.id), None)
    if existing:
        new_qty = existing["quantity"] + qty
        if product.quantity < new_qty:
            if request.is_json:
                return jsonify({"success": False, "error": f"Insufficient stock (have {product.quantity})"}), 400
            flash(f"Insufficient stock for {product.name}.", "warning")
            return redirect(url_for("pos.index"))
        existing["quantity"] = new_qty
        existing["subtotal"] = round(price * new_qty, 2)
    else:
        cart.append({
            "product_id": product.id,
            "name": product.name,
            "price": price,
            "quantity": qty,
            "subtotal": round(subtotal, 2),
        })
    set_cart(cart)
    if request.is_json:
        totals = calculate_cart_totals(cart)
        return jsonify({"success": True, "cart": cart, "totals": totals})
    flash(f"Added {product.name} x{qty}.", "success")
    return redirect(url_for("pos.index"))


@pos_bp.route("/cart/update/<int:product_id>", methods=["POST"])
@login_required
def cart_update(product_id):
    quantity = request.form.get("quantity")
    if quantity is None and request.is_json:
        quantity = request.json.get("quantity")
    if quantity is None:
        if request.is_json:
            return jsonify({"success": False, "error": "quantity required"}), 400
        return redirect(url_for("pos.index"))
    qty = int(quantity)
    cart = get_cart()
    item = next((i for i in cart if i["product_id"] == product_id), None)
    if not item:
        if request.is_json:
            return jsonify({"success": False, "error": "Item not in cart"}), 404
        return redirect(url_for("pos.index"))
    if qty <= 0:
        cart.remove(item)
        set_cart(cart)
        if request.is_json:
            return jsonify({"success": True, "cart": get_cart(), "totals": calculate_cart_totals(get_cart())})
        flash("Item removed from cart.", "info")
        return redirect(url_for("pos.index"))
    product = lookup_product(product_id)
    if not product or product.quantity < qty:
        if request.is_json:
            return jsonify({"success": False, "error": "Insufficient stock"}), 400
        flash("Insufficient stock.", "warning")
        return redirect(url_for("pos.index"))
    item["quantity"] = qty
    item["subtotal"] = round(float(product.price) * qty, 2)
    set_cart(cart)
    if request.is_json:
        return jsonify({"success": True, "cart": get_cart(), "totals": calculate_cart_totals(get_cart())})
    flash("Quantity updated.", "success")
    return redirect(url_for("pos.index"))


@pos_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@login_required
def cart_remove(product_id):
    cart = [i for i in get_cart() if i["product_id"] != product_id]
    set_cart(cart)
    if request.is_json:
        return jsonify({"success": True, "cart": cart, "totals": calculate_cart_totals(cart)})
    flash("Item removed.", "info")
    return redirect(url_for("pos.index"))


@pos_bp.route("/cart/clear", methods=["POST"])
@login_required
def cart_clear():
    set_cart([])
    if request.is_json:
        return jsonify({"success": True, "cart": [], "totals": {}})
    flash("Cart cleared.", "info")
    return redirect(url_for("pos.index"))


@pos_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash("Cart is empty.", "warning")
        return redirect(url_for("pos.index"))
    if request.method == "POST":
        payment_method = (request.form.get("payment_method") or "cash").strip()
        customer_id = request.form.get("customer_id")
        if customer_id is not None and customer_id != "":
            try:
                customer_id = int(customer_id)
            except ValueError:
                customer_id = None
        else:
            customer_id = None
        discount_amount = request.form.get("discount_amount") or 0
        try:
            discount_amount = float(discount_amount)
        except ValueError:
            discount_amount = 0
        promotion_id = request.form.get("promotion_id")
        try:
            promotion_id = int(promotion_id) if promotion_id else None
        except ValueError:
            promotion_id = None
        loyalty_points_used = request.form.get("loyalty_points_used") or 0
        try:
            loyalty_points_used = int(loyalty_points_used)
        except ValueError:
            loyalty_points_used = 0
        sale, err = create_sale(
            user_id=current_user.id,
            cart_items=cart,
            payment_method=payment_method,
            customer_id=customer_id,
            discount_amount=discount_amount,
            loyalty_points_used=loyalty_points_used,
            promotion_id=promotion_id,
        )
        if err:
            flash(err, "danger")
            return redirect(url_for("pos.checkout"))
        log_activity("create", "sale", sale.id, f"Sale #{sale.id} total {sale.total}")
        db.session.commit()
        set_cart([])
        flash(f"Sale completed. Receipt #{sale.id}", "success")
        return redirect(url_for("pos.receipt", sale_id=sale.id))
    totals = calculate_cart_totals(cart)
    promotions = get_active_promotions()
    from app.models.customer import Customer
    customers = Customer.query.order_by(Customer.name).all()
    return render_template("pos/checkout.html", cart=cart, totals=totals, promotions=promotions, customers=customers)


@pos_bp.route("/receipt/<int:sale_id>")
@login_required
def receipt(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        flash("Sale not found.", "danger")
        return redirect(url_for("pos.index"))
    store_name = getattr(Config, "STORE_NAME", "Grocery Store")
    store_address = getattr(Config, "STORE_ADDRESS", "")
    store_phone = getattr(Config, "STORE_PHONE", "")
    return render_template(
        "pos/receipt.html",
        sale=sale,
        store_name=store_name,
        store_address=store_address,
        store_phone=store_phone,
    )


@pos_bp.route("/refund", methods=["GET", "POST"])
@login_required
@manager_required
def refund():
    if request.method == "POST":
        sale_id = request.form.get("sale_id")
        if not sale_id:
            flash("Sale ID required.", "danger")
            return redirect(url_for("pos.refund"))
        try:
            sale_id = int(sale_id)
        except ValueError:
            flash("Invalid sale ID.", "danger")
            return redirect(url_for("pos.refund"))
        full = request.form.get("full_refund") == "1"
        refund_sale, err = create_refund(sale_id, current_user.id, full_refund=full)
        if err:
            flash(err, "danger")
            return redirect(url_for("pos.refund"))
        log_activity("refund", "sale", refund_sale.id, f"Refund for sale #{sale_id}")
        db.session.commit()
        flash(f"Refund processed. Refund # {refund_sale.id}", "success")
        return redirect(url_for("pos.receipt", sale_id=refund_sale.id))
    return render_template("pos/refund.html")

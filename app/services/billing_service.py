"""
Billing / POS: cart totals, tax, discount, checkout, refund.
"""
from decimal import Decimal
from datetime import datetime
from app import db
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.customer import Customer
from app.models.promotion import Promotion
from app.config import Config


def get_tax_rate():
    return Decimal(str(getattr(Config, "TAX_RATE", 0.08)))


def apply_promotion(subtotal, promotion=None):
    """Apply a promotion (percentage or fixed) and return (discount_amount, final_subtotal)."""
    if not promotion or not promotion.is_valid_now():
        return Decimal(0), subtotal
    min_p = promotion.min_purchase or 0
    if subtotal < min_p:
        return Decimal(0), subtotal
    if promotion.promo_type == "percentage":
        discount = (subtotal * promotion.value / 100).quantize(Decimal("0.01"))
    else:
        discount = min(promotion.value, subtotal)
    return discount, subtotal - discount


def calculate_cart_totals(cart_items, discount_amount=None, promotion_id=None):
    """
    cart_items: list of {product_id, name, price, quantity, subtotal}
    Returns dict: subtotal, tax_amount, discount_amount, total.
    """
    subtotal = sum(Decimal(str(item["subtotal"])) for item in cart_items)
    discount = Decimal(str(discount_amount or 0))
    if promotion_id:
        promo = Promotion.query.get(promotion_id)
        if promo and promo.is_valid_now() and (promo.min_purchase or 0) <= subtotal:
            d, _ = apply_promotion(subtotal, promo)
            discount = d
    after_discount = subtotal - discount
    tax = (after_discount * get_tax_rate()).quantize(Decimal("0.01"))
    total = after_discount + tax
    return {
        "subtotal": subtotal,
        "tax_amount": tax,
        "discount_amount": discount,
        "total": total,
    }


def create_sale(user_id, cart_items, payment_method, customer_id=None, discount_amount=0,
                 loyalty_points_used=0, promotion_id=None):
    """
    Create Sale and SaleItems, reduce product quantities. Returns (sale, error_message).
    """
    if not cart_items:
        return None, "Cart is empty"
    totals = calculate_cart_totals(cart_items, discount_amount=discount_amount, promotion_id=promotion_id)
    sale = Sale(
        user_id=user_id,
        customer_id=customer_id,
        subtotal=totals["subtotal"],
        tax_amount=totals["tax_amount"],
        discount_amount=totals["discount_amount"],
        total=totals["total"],
        payment_method=payment_method,
        loyalty_points_used=loyalty_points_used,
    )
    db.session.add(sale)
    db.session.flush()
    loyalty_earned = 0
    for item in cart_items:
        product = Product.query.get(item["product_id"])
        if not product:
            db.session.rollback()
            return None, f"Product {item.get('name')} not found"
        qty = int(item["quantity"])
        if product.quantity < qty:
            db.session.rollback()
            return None, f"Insufficient stock for {product.name} (have {product.quantity})"
        unit_price = Decimal(str(item["price"]))
        subtotal = unit_price * qty
        db.session.add(SaleItem(sale_id=sale.id, product_id=product.id, quantity=qty, unit_price=unit_price, subtotal=subtotal))
        product.quantity -= qty
        loyalty_earned += int(qty)  # simple: 1 point per item (customize as needed)
    sale.loyalty_points_earned = loyalty_earned
    if customer_id:
        cust = Customer.query.get(customer_id)
        if cust:
            cust.loyalty_points = (cust.loyalty_points or 0) - loyalty_points_used + loyalty_earned
    db.session.commit()
    return sale, None


def create_refund(sale_id, user_id, items_to_refund=None, full_refund=True):
    """
    items_to_refund: list of {product_id, quantity}. If full_refund=True, refund all.
    Returns (refund_sale, error).
    """
    sale = Sale.query.get(sale_id)
    if not sale:
        return None, "Sale not found"
    if full_refund:
        items_to_refund = [{"product_id": si.product_id, "quantity": si.quantity} for si in sale.items]
    if not items_to_refund:
        return None, "Nothing to refund"
    cart_items = []
    for ref in items_to_refund:
        si = next((x for x in sale.items if x.product_id == ref["product_id"]), None)
        if not si:
            return None, f"Product {ref['product_id']} not in original sale"
        qty = min(int(ref["quantity"]), si.quantity)
        if qty <= 0:
            continue
        product = Product.query.get(si.product_id)
        product.quantity += qty
        cart_items.append({
            "product_id": product.id,
            "name": product.name,
            "price": str(si.unit_price),
            "quantity": qty,
            "subtotal": str(si.unit_price * qty),
        })
    if not cart_items:
        return None, "No valid items to refund"
    totals = calculate_cart_totals(cart_items)
    refund_sale = Sale(
        user_id=user_id,
        customer_id=sale.customer_id,
        subtotal=-totals["subtotal"],
        tax_amount=-totals["tax_amount"],
        discount_amount=Decimal(0),
        total=-totals["total"],
        payment_method="refund",
    )
    db.session.add(refund_sale)
    db.session.flush()
    for item in cart_items:
        db.session.add(SaleItem(
            sale_id=refund_sale.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=Decimal(item["price"]),
            subtotal=Decimal(item["subtotal"]),
        ))
    db.session.commit()
    return refund_sale, None


def get_active_promotions():
    return Promotion.query.filter_by(active=True).filter(
        (Promotion.valid_from.is_(None)) | (Promotion.valid_from <= datetime.utcnow()),
        (Promotion.valid_to.is_(None)) | (Promotion.valid_to >= datetime.utcnow()),
    ).all()

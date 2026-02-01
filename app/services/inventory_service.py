"""
Inventory business logic: CRUD, batch, alerts, search.
"""
from datetime import date, timedelta
from decimal import Decimal
from app import db
from app.models.product import Product
from app.models.category import Category
from app.models.supplier import Supplier


def get_products_paginated(page=1, per_page=20, category_id=None, search=None, low_stock_only=False):
    q = Product.query
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    if search:
        term = f"%{search}%"
        q = q.filter(
            db.or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.barcode.ilike(term),
            )
        )
    if low_stock_only:
        q = q.filter(Product.quantity <= Product.min_stock)
    q = q.order_by(Product.name)
    return q.paginate(page=page, per_page=per_page, error_out=False)


def get_product_by_id(product_id):
    return Product.query.get(product_id)


def get_product_by_sku(sku):
    return Product.query.filter_by(sku=sku).first()


def get_product_by_barcode(barcode):
    return Product.query.filter_by(barcode=barcode).first()


def lookup_product(identifier):
    """Lookup by id, sku, barcode, or product name (partial match)."""
    if identifier is None:
        return None
    if isinstance(identifier, str):
        identifier = identifier.strip()
        if not identifier:
            return None
    # Try by numeric ID first
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        p = get_product_by_id(int(identifier))
        if p:
            return p
    # Try by SKU (only if non-empty - skip for empty string so we don't match products with null/empty SKU)
    if identifier:
        p = get_product_by_sku(identifier)
        if p:
            return p
        p = get_product_by_barcode(identifier)
        if p:
            return p
    # Fallback: search by product name (first match) so products with no barcode/SKU can be sold
    if isinstance(identifier, str) and len(identifier) >= 1:
        term = f"%{identifier}%"
        p = Product.query.filter(Product.name.ilike(term)).order_by(Product.name).first()
        if p:
            return p
    return None


def add_product(name, price, quantity=0, category_id=None, unit="pcs", expiration_date=None,
                sku=None, barcode=None, supplier_id=None, min_stock=0):
    if sku and get_product_by_sku(sku):
        return None, "SKU already exists"
    if barcode and get_product_by_barcode(barcode):
        return None, "Barcode already exists"
    product = Product(
        name=name,
        price=Decimal(str(price)),
        quantity=int(quantity),
        category_id=category_id,
        unit=unit or "pcs",
        expiration_date=expiration_date,
        sku=sku,
        barcode=barcode,
        supplier_id=supplier_id,
        min_stock=int(min_stock),
    )
    db.session.add(product)
    db.session.commit()
    return product, None


def update_product(product_id, **kwargs):
    product = get_product_by_id(product_id)
    if not product:
        return None, "Product not found"
    sku = kwargs.get("sku")
    if sku is not None and sku != product.sku and get_product_by_sku(sku):
        return None, "SKU already in use"
    barcode = kwargs.get("barcode")
    if barcode is not None and barcode != product.barcode and get_product_by_barcode(barcode):
        return None, "Barcode already in use"
    for key in ("name", "price", "quantity", "category_id", "unit", "expiration_date", "sku", "barcode", "supplier_id", "min_stock"):
        if key in kwargs:
            v = kwargs[key]
            if key == "price":
                v = Decimal(str(v)) if v is not None else Decimal(0)
            if key in ("quantity", "min_stock", "category_id", "supplier_id"):
                v = int(v) if v is not None else 0
            setattr(product, key, v)
    db.session.commit()
    return product, None


def delete_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return False, "Product not found"
    db.session.delete(product)
    db.session.commit()
    return True, None


def batch_update_products(updates):
    """
    updates: list of dicts with at least 'id' and fields to update (quantity, price, etc.)
    Returns (success_count, errors_list).
    """
    success = 0
    errors = []
    for row in updates:
        pid = row.get("id")
        if not pid:
            errors.append("Missing id")
            continue
        product = get_product_by_id(pid)
        if not product:
            errors.append(f"Product id {pid} not found")
            continue
        for key in ("quantity", "price", "min_stock", "name", "unit"):
            if key in row:
                v = row[key]
                if key == "price":
                    product.price = Decimal(str(v))
                elif key == "quantity":
                    product.quantity = int(v)
                elif key == "min_stock":
                    product.min_stock = int(v)
                elif key in ("name", "unit"):
                    setattr(product, key, v)
        success += 1
    db.session.commit()
    return success, errors


def get_low_stock_products():
    return Product.query.filter(Product.quantity <= Product.min_stock).order_by(Product.quantity).all()


def get_expired_or_near_products(days_near=7):
    today = date.today()
    threshold = today + timedelta(days=days_near)
    return Product.query.filter(
        Product.expiration_date.isnot(None),
        Product.expiration_date <= threshold,
    ).order_by(Product.expiration_date).all()


def get_categories_all():
    return Category.query.order_by(Category.name).all()


def get_suppliers_all():
    return Supplier.query.order_by(Supplier.name).all()

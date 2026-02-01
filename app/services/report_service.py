# Analytics and reporting: sales, inventory turnover, exports
from datetime import datetime, date, timedelta
from decimal import Decimal
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from sqlalchemy import func


def sales_report(start_date, end_date, group_by="day"):
    q = db.session.query(
        func.date(Sale.created_at).label("dt"),
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count"),
        func.sum(Sale.tax_amount).label("tax"),
        func.sum(Sale.discount_amount).label("discount"),
    ).filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).group_by(func.date(Sale.created_at)).order_by("dt")
    rows = q.all()
    return [{"period": str(r.dt), "total_sales": float(r.total or 0), "count": r.count, "tax": float(r.tax or 0), "discount": float(r.discount or 0)} for r in rows]


def sales_summary(start_date, end_date):
    q = db.session.query(
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count"),
        func.sum(Sale.tax_amount).label("tax"),
        func.sum(Sale.discount_amount).label("discount"),
    ).filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).first()
    return {
        "total_sales": float(q.total or 0),
        "transaction_count": q.count or 0,
        "total_tax": float(q.tax or 0),
        "total_discount": float(q.discount or 0),
    }


def best_selling_products(start_date, end_date, limit=10):
    q = db.session.query(
        SaleItem.product_id,
        Product.name,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.subtotal).label("revenue"),
    ).join(Product, Product.id == SaleItem.product_id).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).group_by(SaleItem.product_id, Product.name).order_by(func.sum(SaleItem.quantity).desc()).limit(limit)
    return [{"product_id": r.product_id, "name": r.name, "quantity_sold": r.qty, "revenue": float(r.revenue or 0)} for r in q.all()]


def slow_moving_products(limit=10):
    cutoff = datetime.utcnow() - timedelta(days=90)
    sold = db.session.query(SaleItem.product_id, func.sum(SaleItem.quantity).label("qty")).join(
        Sale, Sale.id == SaleItem.sale_id
    ).filter(Sale.created_at >= cutoff, Sale.total > 0).group_by(SaleItem.product_id).subquery()
    q = db.session.query(Product).outerjoin(sold, Product.id == sold.c.product_id).filter(
        func.coalesce(sold.c.qty, 0) < 5
    ).order_by(Product.quantity.desc()).limit(limit)
    return q.all()


def inventory_turnover(start_date, end_date):
    summary = sales_summary(start_date, end_date)
    total_revenue = summary["total_sales"]
    avg_value = db.session.query(func.sum(Product.price * Product.quantity)).scalar() or 0
    return {"total_revenue": total_revenue, "inventory_value_approx": float(avg_value)}


def export_sales_csv(start_date, end_date):
    sales = Sale.query.filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).order_by(Sale.created_at).all()
    yield "sale_id,created_at,user_id,total,tax,discount,payment_method\n"
    for s in sales:
        yield f"{s.id},{s.created_at.isoformat() if s.created_at else ''},{s.user_id},{s.total},{s.tax_amount},{s.discount_amount},{s.payment_method}\n"


def export_sales_excel_io(start_date, end_date):
    try:
        from openpyxl import Workbook
        from io import BytesIO
    except ImportError:
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Sale ID", "Date", "User ID", "Total", "Tax", "Discount", "Payment"])
    sales = Sale.query.filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).order_by(Sale.created_at).all()
    for s in sales:
        ws.append([s.id, s.created_at, s.user_id, float(s.total), float(s.tax_amount), float(s.discount_amount), s.payment_method])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio


def export_sales_pdf_io(start_date, end_date, store_name="Grocery Store"):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
    except ImportError:
        return None
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("Sales Report: %s to %s" % (start_date, end_date), styles["Title"]))
    elements.append(Paragraph(store_name, styles["Normal"]))
    elements.append(Spacer(1, 12))
    sales = Sale.query.filter(
        Sale.total > 0,
        Sale.created_at >= start_date,
        Sale.created_at < end_date + timedelta(days=1),
    ).order_by(Sale.created_at).all()
    data = [["ID", "Date", "Total", "Tax", "Discount", "Payment"]]
    for s in sales:
        data.append([str(s.id), s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "", str(s.total), str(s.tax_amount), str(s.discount_amount), s.payment_method])
    t = Table(data)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey), ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 0), (-1, 0), 12), ("BACKGROUND", (0, 1), (-1, -1), colors.beige), ("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    elements.append(t)
    doc.build(elements)
    bio.seek(0)
    return bio

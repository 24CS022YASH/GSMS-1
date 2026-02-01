# Grocery Store Management System - Implementation Plan

## 1. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Flask 3.x |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (dev) / PostgreSQL (production-ready) |
| Auth | Flask-Login, Werkzeug password hashing |
| Forms | Flask-WTF (validation) |
| Reports | ReportLab (PDF), openpyxl (Excel), csv module |
| Frontend | Jinja2, Bootstrap 5, Chart.js |

## 2. Database Design (ER Overview)

### Core Entities

- **Product**: id, name, category_id, price, quantity, unit, expiration_date, sku, barcode, supplier_id, min_stock, created_at, updated_at
- **Category**: id, name, description
- **Supplier**: id, name, contact, email, phone, address
- **User**: id, username, password_hash, role (admin/manager/cashier), full_name, email, active, created_at
- **Customer**: id, name, email, phone, loyalty_points, created_at
- **Sale**: id, user_id, customer_id (nullable), total, tax, discount, payment_method, created_at
- **SaleItem**: id, sale_id, product_id, quantity, unit_price, subtotal
- **ActivityLog**: id, user_id, action, entity_type, entity_id, details, created_at
- **Shift**: id, user_id, register_id, open_cash, close_cash, start_at, end_at
- **Promotion**: id, name, type (percentage/fixed), value, valid_from, valid_to, min_purchase

### Relationships

- Product → Category (many-to-one), Product → Supplier (many-to-one)
- Sale → User (cashier), Sale → Customer (optional)
- SaleItem → Sale, SaleItem → Product
- ActivityLog → User

## 3. Module Structure

```
app/
├── __init__.py          # App factory
├── config.py
├── models/               # SQLAlchemy models
├── routes/               # Blueprints: auth, inventory, pos, analytics, users, customers
├── services/             # Business logic (inventory, billing, reports)
├── utils/                # Helpers (export PDF/CSV/Excel, barcode)
├── templates/
└── static/
```

## 4. Implementation Phases

### Phase 1: Foundation
- Project setup, config, database models, migrations (Flask-Migrate)
- User model and role-based auth (login, logout, RBAC decorators)
- Activity logging middleware

### Phase 2: Inventory
- Product CRUD, category and supplier management
- Batch import/update (CSV)
- Low stock and expiry alerts API + UI
- Search and filters

### Phase 3: Billing (POS)
- POS UI: product lookup (name/code/barcode), cart, totals, tax, discount
- Checkout: payment method, sale and SaleItem creation
- Receipt generation (print view + PDF)
- Refunds (reverse sale or refund items)
- Loyalty: apply points, redeem, basic offers

### Phase 4: Analytics & Reporting
- Sales reports (daily/weekly/monthly/yearly)
- Inventory turnover, best/slow moving
- Revenue and margin reports
- Export PDF, CSV, Excel
- Charts (Chart.js) for key metrics

### Phase 5: User & Customer Management
- User CRUD, shift and register balancing
- Customer CRUD, purchase history, loyalty points
- Promotions and simple “offers to customers” (e.g. list by segment)

### Phase 6: Extras (if time)
- Barcode generation, supplier orders, multi-store schema prep, offline sync design

## 5. Class Diagram (Key Classes)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Product   │────>│  Category   │     │  Supplier   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id          │     │ id          │     │ id          │
│ name        │     │ name        │     │ name        │
│ category_id │     │ description │     │ contact     │
│ price       │     └─────────────┘     └─────────────┘
│ quantity    │            ^
│ sku/barcode │            │
│ supplier_id │────────────┘
└─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Sale     │────>│  SaleItem   │────>│   Product   │
├─────────────┤     ├─────────────┤     └─────────────┘
│ id          │     │ sale_id     │
│ user_id     │     │ product_id  │     ┌─────────────┐
│ customer_id │     │ quantity    │     │    User     │
│ total, tax  │     │ unit_price  │     ├─────────────┤
│ payment     │     └─────────────┘     │ id, username│
└─────────────┘                         │ role        │
       │                                └─────────────┘
       v
┌─────────────┐
│  Customer   │
├─────────────┤
│ id, name    │
│ loyalty_pts │
└─────────────┘
```

## 6. API / Route Summary

| Area | Routes (examples) |
|------|-------------------|
| Auth | /login, /logout, /profile |
| Inventory | /products, /products/add, /products/<id>/edit, /products/batch, /alerts |
| POS | /pos, /pos/cart/add, /pos/checkout, /pos/receipt/<id>, /pos/refund |
| Analytics | /reports/sales, /reports/inventory, /reports/export |
| Users | /users, /users/<id>, /shifts |
| Customers | /customers, /customers/<id>/history |

## 7. Security & Concurrency

- Passwords: Werkzeug `generate_password_hash` / `check_password_hash`
- RBAC: `@role_required('admin')` etc. on sensitive routes
- CSRF: Flask-WTF on all forms
- Concurrency: SQLite with WAL; for multi-user production use PostgreSQL
- Backup: Scheduled DB copy or pg_dump; optional backup script in `scripts/`

## 8. Next Steps

1. Implement `app/models` and create tables.
2. Implement auth and activity logging.
3. Implement inventory CRUD and alerts.
4. Implement POS flow and receipts.
5. Implement reports and exports.
6. Add user and customer management UIs.
7. Add charts and polish UI.

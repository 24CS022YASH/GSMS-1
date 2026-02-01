"""
Entry point to run the Grocery Store Management System.
"""
import os
from app import create_app, db
from app.models import User, Category, Supplier

# Ensure instance folder exists for SQLite
os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Create tables and seed initial data."""
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username="admin").first() is None:
            admin = User(
                username="admin",
                role="admin",
                full_name="Administrator",
            )
            admin.set_password("admin123")
            db.session.add(admin)
        if Category.query.count() == 0:
            for name in ["Dairy", "Bakery", "Beverages", "Produce", "Frozen", "Snacks"]:
                db.session.add(Category(name=name))
        db.session.commit()
    print("Database initialized. Default admin: admin / admin123")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

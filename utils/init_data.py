# utils/init_data.py
from extensions import db
from models.user import UserModel
from utils.security import hash_password
from sqlalchemy.exc import OperationalError
from sqlalchemy import inspect

def create_default_super_admin():
    try:
        # ✅ Corrected: inspect returns table names as strings
        inspector = inspect(db.engine)
        if "users" not in inspector.get_table_names():
            return

        admin_exists = UserModel.query.filter_by(role="super_admin").first()
        if not admin_exists:
            password = hash_password("admin123")
            admin = UserModel(
                name="Super Admin",
                email="admin@system.com",
                password=password,
                role="super_admin"
            )
            db.session.add(admin)
            db.session.commit()
    except OperationalError:
        # DB might not be ready yet
        pass
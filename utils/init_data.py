# utils/init_data.py

from models.user import UserModel
from utils.security import hash_password
from extensions import db

def create_default_super_admin():
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
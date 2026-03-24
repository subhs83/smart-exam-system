# test_db.py
from app import create_app
from extensions import db
from models.user import UserModel

app = create_app()

with app.app_context():
    users = UserModel.query.all()
    if not users:
        print("No users found in DB.")
    else:
        print("Users in DB:")
        for user in users:
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}")
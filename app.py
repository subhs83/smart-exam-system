# app.py
import os
from flask import Flask, render_template
from config import Config
from extensions import login_manager, db, migrate

# Blueprints
from blueprints.auth import auth_bp
from blueprints.super_admin import super_admin_bp
from blueprints.school_admin import school_admin_bp
from blueprints.teacher import teacher_bp
from blueprints.student import student_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Import models for migrations
    import models
    from models.user import UserModel

    @login_manager.user_loader
    def load_user(user_id):
        return UserModel.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(school_admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    return app

# ✅ Only run server and init super admin when executed directly
if __name__ == "__main__":
    app = create_app()

    from utils.init_data import create_default_super_admin
    from extensions import db
    from sqlalchemy import inspect

    # Run super admin initialization safely inside app context
    with app.app_context():
        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            create_default_super_admin()

    app.run(debug=True)
# app.py
from flask import Flask, render_template
from config import Config
from extensions import login_manager, db
from utils.init_data import create_default_super_admin
import os

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

    # Ensure uploads folder exists
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # Import User here to avoid circular imports
    from models.user import UserModel  # make sure this matches your model name

    @login_manager.user_loader
    def load_user(user_id):
        return UserModel.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(school_admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    # Optional: Create tables if not using migrations
    with app.app_context():
         create_default_super_admin()
    #     db.create_all()

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
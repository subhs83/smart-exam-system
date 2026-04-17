import os
from flask import Flask, render_template
from config import Config
from .extensions import login_manager, db, migrate

# Blueprints
from .blueprints.auth import auth_bp
from .blueprints.super_admin import super_admin_bp
from .blueprints.school_admin import school_admin_bp
from .blueprints.teacher import teacher_bp
from .blueprints.student import student_bp
from .blueprints.home import home_bp
from .blueprints.footer import footer_bp



def create_app():
    # BASE_DIR = project root
    base_dir = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),  # templates outside package
        static_folder=os.path.join(base_dir, "static")       # static outside package
    )
    app.config.from_object(Config)

    # Initialize extensions
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models for migrations
    from .models.user import UserModel

    @login_manager.user_loader
    def load_user(user_id):
        return UserModel.query.get(int(user_id))

    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(school_admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(footer_bp)


    return app
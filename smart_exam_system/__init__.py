import os
from flask import Flask
from .config import Config
from .extensions import login_manager, db, migrate

# Blueprints
from .blueprints.auth import auth_bp
from .blueprints.super_admin import super_admin_bp
from .blueprints.school_admin import school_admin_bp
from .blueprints.teacher import teacher_bp
from .blueprints.student import student_bp
from .blueprints.home import home_bp
from .blueprints.footer import footer_bp

from .utils.init_data import create_default_super_admin


def create_app():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )

    # Config
    app.config.from_object(Config)

    # Extensions
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    # User loader
    from .models.user import UserModel

    @login_manager.user_loader
    def load_user(user_id):
        return UserModel.query.get(int(user_id))

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(school_admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(footer_bp)

    # Safe startup task (NO db.create_all)
    with app.app_context():
         db.create_all()
         create_default_super_admin()

    return app

# 👇 THIS IS THE IMPORTANT PART
app = create_app()    
from sqlalchemy import text

@app.route("/fix-db")
def fix_db():
    try:
        db.session.execute(text("ALTER TABLE demo_requests ADD COLUMN phone VARCHAR(20);"))
        db.session.execute(text("ALTER TABLE demo_requests ADD COLUMN size VARCHAR(20);"))
        db.session.commit()
        return "DB Updated Successfully"
    except Exception as e:
        return str(e)
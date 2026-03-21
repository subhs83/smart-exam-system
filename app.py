from flask import Flask, render_template
from config import Config 
from extensions import login_manager,db
from database import init_db
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
    login_manager.init_app(app)
    db.init_app(app)

    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # Import User here (safe, avoids circular import) 
    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(super_admin_bp)
    app.register_blueprint(school_admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    with app.app_context():
        init_db()

    @app.route("/")
    def home():
        return render_template("home.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    url_prefix="/auth"
)

# Import routes after blueprint is created
from smart_exam_system.blueprints.auth import routes
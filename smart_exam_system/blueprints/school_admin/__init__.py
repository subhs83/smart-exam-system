from flask import Blueprint

school_admin_bp = Blueprint(
    "school_admin", __name__,
    template_folder="templates",
    url_prefix="/school_admin"
)

from smart_exam_system.blueprints.school_admin import routes

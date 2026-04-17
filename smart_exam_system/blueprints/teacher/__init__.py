from flask import Blueprint

teacher_bp = Blueprint(
    "teacher",__name__,
    template_folder="templates",
    url_prefix="/teacher"
)

from smart_exam_system.blueprints.teacher import routes

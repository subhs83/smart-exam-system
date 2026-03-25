from flask import Blueprint

student_bp = Blueprint(
    "student",__name__,
    template_folder="templates",
    url_prefix="/student"
)

from smart_exam_system.blueprints.student import routes
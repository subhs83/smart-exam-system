from flask import Blueprint

student_bp = Blueprint(
    "student",__name__,
    template_folder="templates",
    url_prefix="/student"
)

from . import routes
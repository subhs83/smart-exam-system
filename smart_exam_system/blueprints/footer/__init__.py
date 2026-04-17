from flask import Blueprint

footer_bp = Blueprint(
    "footer", __name__,
    template_folder="templates",
    url_prefix="/"
)

from smart_exam_system.blueprints.footer import routes

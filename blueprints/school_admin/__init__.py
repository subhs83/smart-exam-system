from flask import Blueprint

school_admin_bp = Blueprint(
    "school_admin", __name__,
    template_folder="templates",
    url_prefix="/school_admin"
)

from . import routes

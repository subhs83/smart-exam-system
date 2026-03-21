from flask import Blueprint

super_admin_bp = Blueprint(
    "super_admin", __name__,
    template_folder="templates",
    url_prefix="/super_admin"
)

from . import routes  # ensures routes are registered

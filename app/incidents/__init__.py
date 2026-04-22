from flask import Blueprint

bp = Blueprint('incidents', __name__, url_prefix='/incidents')

from app.incidents import routes  # noqa: E402, F401

from flask import Blueprint

bp = Blueprint('bms', __name__)

from . import routes 
from flask import Blueprint

bp = Blueprint('bms', __name__)

from app.bms import routes 
from flask import Blueprint, send_from_directory
import os

bp = Blueprint('api', __name__)

@bp.route('/swagger')
def swagger():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'swagger.yaml')

from . import routes 
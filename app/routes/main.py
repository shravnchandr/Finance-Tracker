from flask import Blueprint, render_template, session
from app.utils import login_required

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    role = session.get('role')
    username = session.get('username')
    return render_template('index.html', username=username, role=role)

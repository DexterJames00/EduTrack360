from flask import Blueprint, render_template

main_admin_bp = Blueprint('main_admin', __name__, url_prefix='/main_admin')

@main_admin_bp.route('/')
def dashboard():
    return render_template('main_admin/main_admin_dashboard.html')

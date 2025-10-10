from flask import Blueprint
from .crud_dashboard import dashboard_bp
from .crud_attendance import attendance_bp
from .crud_schedule import schedule_bp
from .crud_messaging import messaging_bp

# Create main instructor blueprint
instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor', template_folder='templates')

# Register all sub-blueprints
instructor_bp.register_blueprint(dashboard_bp)
instructor_bp.register_blueprint(attendance_bp)
instructor_bp.register_blueprint(schedule_bp) 
instructor_bp.register_blueprint(messaging_bp)

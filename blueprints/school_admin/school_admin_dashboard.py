from flask import Blueprint, render_template, request, redirect, url_for, flash

# Import all CRUD modules with correct blueprint names
from .crud_accounts import school_admin_bp as crud_accounts_bp
from .crud_intructor import school_admin_bp as crud_instructors_bp
from .crud_section import school_admin_bp as crud_sections_bp
from .crud_student import school_admin_bp as crud_students_bp
from .crud_subject import school_admin_bp as crud_subjects_bp
from .crud_assignment import assignment_bp as crud_assignment_bp

school_admin_bp = Blueprint('school_admin', __name__, url_prefix='/school_admin')

# Register all CRUD blueprints
school_admin_bp.register_blueprint(crud_accounts_bp)
school_admin_bp.register_blueprint(crud_instructors_bp)
school_admin_bp.register_blueprint(crud_sections_bp)
school_admin_bp.register_blueprint(crud_students_bp)
school_admin_bp.register_blueprint(crud_subjects_bp)
school_admin_bp.register_blueprint(crud_assignment_bp)

# Dashboard
@school_admin_bp.route('/')
def dashboard():
    return render_template('school_admin/school_admin_dashboard.html')



# Sections
@school_admin_bp.route('/sections')
def sections():
    return render_template('school_admin/school_admin_sections.html')

# Attendance
@school_admin_bp.route('/attendance')
def attendance():
    return render_template('school_admin/school_admin_attendance.html')

# Notifications
@school_admin_bp.route('/notifications')
def notifications():
    return render_template('school_admin/school_admin_notifications.html')

# ------------------------------
# Telegram Bot Configuration
# ------------------------------
# NOTE: Telegram routes moved to crud_telegram.py
# @school_admin_bp.route('/telegram', methods=['GET'])
# def telegram_config():
#     # Fetch stats from database (example placeholders)
#     linked_parents_count = 42
#     unlinked_parents_count = 18
#     return render_template(
#         'school_admin/telegram_config.html',
#         linked_parents_count=linked_parents_count,
#         unlinked_parents_count=unlinked_parents_count
#     )

# @school_admin_bp.route('/telegram/configure', methods=['POST'])
# def configure_telegram():
#     bot_token = request.form.get('bot_token')
#     bot_username = request.form.get('bot_username')
#     # TODO: Save these to the database
#     flash(f'Telegram bot {bot_username} configured successfully!', 'success')
#     return redirect(url_for('school_admin.telegram_config'))

# @school_admin_bp.route('/telegram/test', methods=['POST'])
# def test_telegram():
#     test_message = request.form.get('test_message')
#     # TODO: Send test message via Telegram API
#     flash('Test message sent successfully!', 'success')
#     return redirect(url_for('school_admin.telegram_config'))

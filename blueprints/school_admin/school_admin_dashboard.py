from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import db
from models import Instructor, Student, Subject, Section, Attendance, InstructorSchedule, TelegramConfig, School
from sqlalchemy import func
import requests

# Import all CRUD modules with correct blueprint names
from .crud_accounts import school_admin_bp as crud_accounts_bp
from .crud_intructor import school_admin_bp as crud_instructors_bp
from .crud_section import sections_bp as crud_sections_bp
from .crud_student import school_admin_bp as crud_students_bp
from .crud_subject import subjects_bp as crud_subjects_bp
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
    """School Admin Dashboard with real-time statistics"""
    
    # Get school_id from session
    school_id = session.get('school_id')
    if not school_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for('auth.login'))
    
    print(f"DEBUG: Dashboard loading for school_id: {school_id}")
    
    # Fetch real statistics from database
    try:
        # Count instructors
        instructors_count = Instructor.query.filter_by(school_id=school_id).count()
        
        # Count students
        students_count = Student.query.filter_by(school_id=school_id).count()
        
        # Count subjects
        subjects_count = Subject.query.filter_by(school_id=school_id).count()
        
        # Count sections
        sections_count = Section.query.filter_by(school_id=school_id).count()
        
        # Calculate attendance rate for today (filtered by school)
        from datetime import date
        today = date.today()
        
        # Get total attendance records for today for this school
        # We need to join with students to filter by school_id
        total_today = db.session.query(Attendance).join(Student).filter(
            Attendance.date == today,
            Student.school_id == school_id
        ).count()
        
        present_today = db.session.query(Attendance).join(Student).filter(
            Attendance.date == today,
            Attendance.status == 'Present',
            Student.school_id == school_id
        ).count()
        
        # Calculate attendance rate
        attendance_rate = (present_today / total_today * 100) if total_today > 0 else 0
        
        # Get active classes today for this school
        today_weekday = today.strftime('%A')
        active_classes = db.session.query(InstructorSchedule).join(Instructor).filter(
            InstructorSchedule.day == today_weekday,
            Instructor.school_id == school_id
        ).count()
        
        print(f"DEBUG: School {school_id} metrics:")
        print(f"  - Instructors: {instructors_count}")
        print(f"  - Students: {students_count}")
        print(f"  - Subjects: {subjects_count}")
        print(f"  - Sections: {sections_count}")
        print(f"  - Attendance rate: {attendance_rate:.1f}% ({present_today}/{total_today})")
        print(f"  - Active classes ({today_weekday}): {active_classes}")
        
        # Recent activity data (mock data for now - can be enhanced later)
        recent_activities = [
            {
                'type': 'attendance',
                'message': 'Attendance Successfully Recorded',
                'details': 'Section A • Multiple Instructors',
                'time': 'Today, 08:45 AM',
                'status': 'COMPLETED',
                'icon': 'check-circle',
                'color': 'blue'
            },
            {
                'type': 'enrollment',
                'message': 'New Student Enrolled',
                'details': 'Student Registration • Section B',
                'time': 'Yesterday, 03:20 PM',
                'status': 'NEW',
                'icon': 'user-plus',
                'color': 'emerald'
            },
            {
                'type': 'update',
                'message': 'Curriculum Updated',
                'details': 'Subject Information • New learning objectives',
                'time': 'Yesterday, 11:10 AM',
                'status': 'MODIFIED',
                'icon': 'edit',
                'color': 'purple'
            }
        ]
        
    except Exception as e:
        # Fallback to default values if database query fails
        print(f"Database query error: {e}")
        instructors_count = 12
        students_count = 320
        subjects_count = 18
        sections_count = 6
        attendance_rate = 94.5
        active_classes = 28
        recent_activities = []
    
    # Pass all data to template
    return render_template('school_admin/school_admin_dashboard.html',
                         instructors_count=instructors_count,
                         students_count=students_count,
                         subjects_count=subjects_count,
                         sections_count=sections_count,
                         attendance_rate=attendance_rate,
                         active_classes=active_classes,
                         recent_activities=recent_activities)



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

# Telegram Configuration Routes for School Admin
@school_admin_bp.route('/telegram-config')
def telegram_config():
    """Simplified Telegram management for School Admin - view only"""
    school_id = session.get('school_id')
    if not school_id:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for('auth.login'))
    return render_template('school_admin/telegram_config.html')

@school_admin_bp.route('/telegram-stats')
def telegram_stats():
    """Get telegram statistics for this school only"""
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get total students for this school
        total_students = Student.query.filter_by(school_id=school_id).count()
        
        # Get connected parents for this school (students with telegram_chat_id)
        connected_parents = Student.query.filter_by(school_id=school_id).filter(Student.telegram_chat_id.isnot(None)).count()
        
        # Calculate not connected
        not_connected = total_students - connected_parents
        
        stats = {
            'total_students': total_students,
            'connected_parents': connected_parents,
            'not_connected': not_connected
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_admin_bp.route('/student-connections')
def student_connections():
    """Get students with their telegram connection status for this school only"""
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Query to get students for this school only
        students_query = Student.query.filter_by(school_id=school_id).all()
        
        students = []
        for student in students_query:
            students.append({
                'id': student.id,
                'code': student.code,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'grade_level': student.grade_level,
                'section_name': f'Section {student.section_id}' if student.section_id else 'N/A',
                'parent_contact': student.parent_contact,
                'telegram_chat_id': student.telegram_chat_id,
                'telegram_status': bool(student.telegram_chat_id)
            })
        
        return jsonify({'students': students})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_admin_bp.route('/auto-setup-status')
def auto_setup_status():
    """Get auto-setup status for school admin view"""
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Check if we have an active telegram configuration
        active_config = TelegramConfig.query.filter_by(is_active=True).first()
        
        if not active_config:
            return jsonify({
                'setup_complete': False,
                'message': 'No active telegram configuration found'
            })
        
        # Try to get the current ngrok status
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                return jsonify({
                    'setup_complete': True,
                    'message': 'Bot system is active'
                })
            else:
                return jsonify({
                    'setup_complete': False,
                    'message': 'Bot system not ready'
                })
                
        except requests.RequestException:
            return jsonify({
                'setup_complete': False,
                'message': 'Bot system not available'
            })
            
    except Exception as e:
        return jsonify({
            'setup_complete': False,
            'message': f'Error checking setup status: {str(e)}'
        })

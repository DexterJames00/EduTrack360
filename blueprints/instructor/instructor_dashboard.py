from flask import Blueprint, render_template

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor', template_folder='templates')

@instructor_bp.route('/')
def dashboard():
    return render_template('instructor/instructor_dashboard.html')

# New route for schedule list and attendance
@instructor_bp.route('/attendance', methods=['GET'])
def attendance_sched():
    # Mock schedule data
    schedules = [
        {'id': 101, 'subject': 'Math 101', 'section': 'A', 'time': '08:00 AM'},
        {'id': 102, 'subject': 'Science 201', 'section': 'B', 'time': '10:00 AM'},
        {'id': 103, 'subject': 'English 301', 'section': 'C', 'time': '01:00 PM'},
        {'id': 101, 'subject': 'Math 101', 'section': 'A', 'time': '08:00 AM'},
        {'id': 102, 'subject': 'Science 201', 'section': 'B', 'time': '10:00 AM'},
        {'id': 103, 'subject': 'English 301', 'section': 'C', 'time': '01:00 PM'}
    ]
    return render_template('instructor/attendance_sched.html', schedules=schedules)

@instructor_bp.route('/attendance/<int:sched_id>', methods=['GET', 'POST'])
def record_attendance(sched_id):
    # Mock lookup for schedule and students
    schedule = next((s for s in [
        {'id': 101, 'subject': 'Math 101', 'section': 'A', 'time': '08:00 AM'},
        {'id': 102, 'subject': 'Science 201', 'section': 'B', 'time': '10:00 AM'},
        {'id': 103, 'subject': 'English 301', 'section': 'C', 'time': '01:00 PM'}
    ] if s['id'] == sched_id), None)
    students = [
        {'id': 1, 'name': 'Alice Johnson'},
        {'id': 2, 'name': 'Bob Smith'},
        {'id': 3, 'name': 'Charlie Lee'}
    ]
    return render_template('instructor/record_attendance.html', schedule=schedule, students=students)

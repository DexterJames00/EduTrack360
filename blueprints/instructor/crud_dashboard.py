from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import (
    Instructor, InstructorSchedule, Attendance, Student, Subject, Section, 
    Notification, TelegramConfig
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, distinct

dashboard_bp = Blueprint('instructor_dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def dashboard():
    """Main instructor dashboard"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    instructor_name = session.get('instructor_name', 'Instructor')
    
    # Get dashboard data
    dashboard_data = get_dashboard_data(instructor_id, school_id)
    
    return render_template(
        'instructor/instructor_dashboard.html',
        instructor_name=instructor_name,
        data=dashboard_data
    )

def get_dashboard_data(instructor_id, school_id):
    """Get comprehensive dashboard data"""
    today = date.today()
    current_time = datetime.now()
    
    # Today's schedule
    todays_schedule = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        Subject.name.label('subject'),
        Section.name.label('section'),
        Section.grade_level
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .filter(InstructorSchedule.day == today.strftime('%A'))\
     .order_by(InstructorSchedule.time)\
     .all()
    
    # Attendance submitted today
    todays_attendance = db.session.query(distinct(Attendance.subject_id))\
        .filter(Attendance.instructor_id == instructor_id)\
        .filter(Attendance.date == today)\
        .count()
    
    # Recent attendance records
    recent_attendance = db.session.query(
        Attendance.date,
        Subject.name.label('subject'),
        Section.name.label('section'),
        func.count(Attendance.id).label('total_students'),
        func.sum(func.if_(Attendance.status == 'Present', 1, 0)).label('present_count'),
        func.sum(func.if_(Attendance.status == 'Absent', 1, 0)).label('absent_count'),
        func.sum(func.if_(Attendance.status == 'Late', 1, 0)).label('late_count')
    ).join(Subject, Attendance.subject_id == Subject.id)\
     .join(Student, Attendance.student_id == Student.id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Attendance.instructor_id == instructor_id)\
     .group_by(Attendance.date, Subject.name, Section.name)\
     .order_by(Attendance.date.desc())\
     .limit(10)\
     .all()
    
    # Weekly attendance summary
    week_start = today - timedelta(days=today.weekday())
    weekly_stats = db.session.query(
        func.count(Attendance.id).label('total_records'),
        func.sum(func.if_(Attendance.status == 'Present', 1, 0)).label('present'),
        func.sum(func.if_(Attendance.status == 'Absent', 1, 0)).label('absent'),
        func.sum(func.if_(Attendance.status == 'Late', 1, 0)).label('late')
    ).filter(Attendance.instructor_id == instructor_id)\
     .filter(Attendance.date >= week_start)\
     .first()
    
    # Students with poor attendance (< 80%)
    poor_attendance = db.session.query(
        Student.id,
        func.concat(Student.first_name, ' ', Student.last_name).label('name'),
        Section.name.label('section'),
        func.count(Attendance.id).label('total_classes'),
        func.sum(func.if_(Attendance.status == 'Present', 1, 0)).label('present_count')
    ).join(Attendance, Student.id == Attendance.student_id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Attendance.instructor_id == instructor_id)\
     .filter(Attendance.date >= (today - timedelta(days=30)))\
     .group_by(Student.id)\
     .having(func.sum(func.if_(Attendance.status == 'Present', 1, 0)) / func.count(Attendance.id) < 0.8)\
     .limit(5)\
     .all()
    
    # Messages sent today
    todays_messages = Notification.query.join(Student)\
        .filter(Student.school_id == school_id)\
        .filter(func.date(Notification.timestamp) == today)\
        .count()
    
    # Upcoming classes (next 3)
    current_day = current_time.strftime('%A')
    current_time_str = current_time.strftime('%H:%M')
    
    upcoming_classes = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        Subject.name.label('subject'),
        Section.name.label('section')
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .filter(InstructorSchedule.day == current_day)\
     .filter(InstructorSchedule.time >= current_time_str)\
     .order_by(InstructorSchedule.time)\
     .limit(3)\
     .all()
    
    # Total students under instructor
    total_students = db.session.query(func.count(distinct(Student.id)))\
        .join(InstructorSchedule, Student.section_id == InstructorSchedule.section_id)\
        .filter(InstructorSchedule.instructor_id == instructor_id)\
        .scalar()
    
    # Students with Telegram connected
    telegram_connected = db.session.query(func.count(distinct(Student.id)))\
        .join(InstructorSchedule, Student.section_id == InstructorSchedule.section_id)\
        .filter(InstructorSchedule.instructor_id == instructor_id)\
        .filter(Student.telegram_chat_id.isnot(None))\
        .scalar()
    
    return {
        'todays_schedule': todays_schedule,
        'todays_classes_count': len(todays_schedule),
        'attendance_submitted': todays_attendance,
        'recent_attendance': recent_attendance,
        'weekly_stats': {
            'total_records': weekly_stats.total_records or 0,
            'present': weekly_stats.present or 0,
            'absent': weekly_stats.absent or 0,
            'late': weekly_stats.late or 0,
            'attendance_rate': round((weekly_stats.present / weekly_stats.total_records * 100) if weekly_stats.total_records else 0, 1)
        },
        'poor_attendance': poor_attendance,
        'todays_messages': todays_messages,
        'upcoming_classes': upcoming_classes,
        'total_students': total_students,
        'telegram_connected': telegram_connected,
        'telegram_rate': round((telegram_connected / total_students * 100) if total_students else 0, 1)
    }

@dashboard_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint for dashboard statistics"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    data = get_dashboard_data(instructor_id, school_id)
    return jsonify(data)

@dashboard_bp.route('/api/attendance-chart', methods=['GET'])
def attendance_chart_data():
    """Get attendance data for charts"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    days = int(request.args.get('days', 7))
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Daily attendance data
    daily_data = db.session.query(
        Attendance.date,
        func.sum(func.if_(Attendance.status == 'Present', 1, 0)).label('present'),
        func.sum(func.if_(Attendance.status == 'Absent', 1, 0)).label('absent'),
        func.sum(func.if_(Attendance.status == 'Late', 1, 0)).label('late')
    ).filter(Attendance.instructor_id == instructor_id)\
     .filter(Attendance.date >= start_date)\
     .filter(Attendance.date <= end_date)\
     .group_by(Attendance.date)\
     .order_by(Attendance.date)\
     .all()
    
    chart_data = {
        'labels': [],
        'present': [],
        'absent': [],
        'late': []
    }
    
    for data in daily_data:
        chart_data['labels'].append(data.date.strftime('%m/%d'))
        chart_data['present'].append(data.present or 0)
        chart_data['absent'].append(data.absent or 0)
        chart_data['late'].append(data.late or 0)
    
    return jsonify(chart_data)

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
def instructor_profile():
    """View and edit instructor profile"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    instructor = Instructor.query.get(instructor_id)
    
    if not instructor:
        flash('Instructor not found', 'error')
        return redirect(url_for('instructor_dashboard.dashboard'))
    
    if request.method == 'POST':
        try:
            # Update instructor information
            instructor.name = request.form.get('name', instructor.name)
            instructor.email = request.form.get('email', instructor.email)
            instructor.address = request.form.get('address', instructor.address)
            instructor.gender = request.form.get('gender', instructor.gender)
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('instructor/profile.html', instructor=instructor)

@dashboard_bp.route('/notifications', methods=['GET'])
def notifications():
    """View instructor notifications and alerts"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    # Get recent message history
    messages = db.session.query(
        Notification.id,
        Notification.message,
        Notification.status,
        Notification.timestamp,
        func.concat(Student.first_name, ' ', Student.last_name).label('student_name'),
        Section.name.label('section')
    ).join(Student, Notification.student_id == Student.id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Student.school_id == school_id)\
     .order_by(Notification.timestamp.desc())\
     .limit(20)\
     .all()
    
    return render_template('instructor/notifications.html', messages=messages)
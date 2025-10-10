from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import InstructorSchedule, Subject, Section, Instructor
from datetime import datetime, timedelta
from sqlalchemy import func, and_

schedule_bp = Blueprint('instructor_schedule', __name__)

@schedule_bp.route('/schedule', methods=['GET'])
def view_schedule():
    """View instructor's weekly schedule"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    # Get all schedules for the instructor
    schedules = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        InstructorSchedule.day,
        Subject.name.label('subject'),
        Subject.grade_level.label('subject_grade'),
        Section.name.label('section'),
        Section.grade_level.label('section_grade')
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .filter(Subject.school_id == school_id)\
     .order_by(InstructorSchedule.day, InstructorSchedule.time)\
     .all()
    
    # Organize schedules by day
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_schedule = {day: [] for day in days}
    
    for schedule in schedules:
        if schedule.day in weekly_schedule:
            weekly_schedule[schedule.day].append(schedule)
    
    return render_template('instructor/schedule.html', weekly_schedule=weekly_schedule, days=days)

@schedule_bp.route('/schedule/today', methods=['GET'])
def todays_schedule():
    """Get today's schedule for instructor dashboard"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    today = datetime.now().strftime('%A')
    
    # Get today's schedules
    schedules = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        Subject.name.label('subject'),
        Section.name.label('section'),
        Section.grade_level
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .filter(InstructorSchedule.day == today)\
     .order_by(InstructorSchedule.time)\
     .all()
    
    schedule_list = []
    for schedule in schedules:
        schedule_list.append({
            'id': schedule.id,
            'time': schedule.time,
            'subject': schedule.subject,
            'section': schedule.section,
            'grade_level': schedule.grade_level
        })
    
    return jsonify({'schedules': schedule_list})

@schedule_bp.route('/schedule/upcoming', methods=['GET'])
def upcoming_classes():
    """Get upcoming classes for the instructor"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    current_time = datetime.now()
    current_day = current_time.strftime('%A')
    current_time_str = current_time.strftime('%H:%M')
    
    # Get today's remaining schedules
    todays_remaining = db.session.query(
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
    
    upcoming = []
    for schedule in todays_remaining:
        upcoming.append({
            'id': schedule.id,
            'time': schedule.time,
            'subject': schedule.subject,
            'section': schedule.section,
            'day': 'Today'
        })
    
    return jsonify({'upcoming': upcoming})

@schedule_bp.route('/schedule/conflicts', methods=['GET'])
def check_conflicts():
    """Check for scheduling conflicts"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    
    # Find overlapping schedules (same day and time)
    conflicts = db.session.query(
        InstructorSchedule.day,
        InstructorSchedule.time,
        func.count(InstructorSchedule.id).label('conflict_count'),
        func.group_concat(Subject.name).label('subjects')
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .group_by(InstructorSchedule.day, InstructorSchedule.time)\
     .having(func.count(InstructorSchedule.id) > 1)\
     .all()
    
    conflict_list = []
    for conflict in conflicts:
        conflict_list.append({
            'day': conflict.day,
            'time': conflict.time,
            'count': conflict.conflict_count,
            'subjects': conflict.subjects.split(',') if conflict.subjects else []
        })
    
    return jsonify({'conflicts': conflict_list})

@schedule_bp.route('/schedule/summary', methods=['GET'])
def schedule_summary():
    """Get weekly schedule summary"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    
    # Get schedule summary by day
    summary = db.session.query(
        InstructorSchedule.day,
        func.count(InstructorSchedule.id).label('class_count'),
        func.min(InstructorSchedule.time).label('first_class'),
        func.max(InstructorSchedule.time).label('last_class')
    ).filter(InstructorSchedule.instructor_id == instructor_id)\
     .group_by(InstructorSchedule.day)\
     .all()
    
    summary_data = {}
    for day_summary in summary:
        summary_data[day_summary.day] = {
            'class_count': day_summary.class_count,
            'first_class': day_summary.first_class,
            'last_class': day_summary.last_class
        }
    
    return jsonify({'summary': summary_data})

@schedule_bp.route('/schedule/<int:schedule_id>/students', methods=['GET'])
def schedule_students(schedule_id):
    """Get students for a specific schedule"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    
    # Verify instructor owns this schedule
    schedule = InstructorSchedule.query.filter_by(
        id=schedule_id,
        instructor_id=instructor_id
    ).first()
    
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    # Get students in the section
    from models import Student
    students = db.session.query(
        Student.id,
        Student.first_name,
        Student.last_name,
        Student.telegram_status,
        func.concat(Student.first_name, ' ', Student.last_name).label('full_name')
    ).filter(Student.section_id == schedule.section_id)\
     .order_by(Student.first_name, Student.last_name)\
     .all()
    
    student_list = []
    for student in students:
        student_list.append({
            'id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'full_name': student.full_name,
            'telegram_connected': student.telegram_status
        })
    
    return jsonify({'students': student_list})
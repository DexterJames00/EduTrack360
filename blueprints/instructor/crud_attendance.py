from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import Attendance, Student, Subject, InstructorSchedule, Section, Instructor
from datetime import datetime, date
from sqlalchemy import func

attendance_bp = Blueprint('instructor_attendance', __name__)

@attendance_bp.route('/attendance', methods=['GET'])
def attendance_schedule_list():
    """Display list of instructor's schedules for attendance recording"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    # Get instructor's schedules with subject and section details
    schedules = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        InstructorSchedule.day,
        Subject.name.label('subject'),
        Section.name.label('section'),
        Section.grade_level,
        Instructor.name.label('instructor_name')
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .filter(Subject.school_id == school_id)\
     .all()
    
    return render_template('instructor/attendance_sched.html', schedules=schedules, year=datetime.now().year)

@attendance_bp.route('/attendance/<int:sched_id>', methods=['GET', 'POST'])
def record_attendance(sched_id):
    """Record attendance for a specific schedule"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    # Get schedule details
    schedule = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        InstructorSchedule.day,
        InstructorSchedule.subject_id,
        InstructorSchedule.section_id,
        Subject.name.label('subject'),
        Section.name.label('section'),
        Section.grade_level
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(InstructorSchedule.id == sched_id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .first()
    
    if not schedule:
        flash('Schedule not found or access denied', 'error')
        return redirect(url_for('instructor_attendance.attendance_schedule_list'))
    
    # Get students in the section
    students = db.session.query(
        Student.id,
        func.concat(Student.first_name, ' ', Student.last_name).label('name'),
        Student.telegram_chat_id,
        Student.telegram_status
    ).filter(Student.section_id == schedule.section_id)\
     .filter(Student.school_id == school_id)\
     .order_by(Student.first_name, Student.last_name)\
     .all()
    
    if request.method == 'POST':
        try:
            attendance_date = request.form.get('date')
            if not attendance_date:
                flash('Please select a date', 'error')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            
            # Check if attendance already exists for this date
            existing_attendance = Attendance.query.filter_by(
                date=attendance_date,
                subject_id=schedule.subject_id,
                instructor_id=instructor_id
            ).first()
            
            if existing_attendance:
                flash(f'Attendance for {attendance_date} has already been recorded', 'warning')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            # Process attendance for each student
            attendance_records = []
            for student in students:
                status = request.form.get(f'status_{student.id}', 'Present')
                
                attendance_record = Attendance(
                    student_id=student.id,
                    date=attendance_date,
                    status=status,
                    subject_id=schedule.subject_id,
                    instructor_id=instructor_id
                )
                attendance_records.append(attendance_record)
            
            # Save all attendance records
            db.session.add_all(attendance_records)
            db.session.commit()
            
            flash(f'Attendance recorded successfully for {len(attendance_records)} students', 'success')
            return redirect(url_for('instructor_attendance.attendance_schedule_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording attendance: {str(e)}', 'error')
    
    return render_template('instructor/record_attendance.html', schedule=schedule, students=students)

@attendance_bp.route('/attendance/history', methods=['GET'])
def attendance_history():
    """View attendance history for instructor"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    
    # Get attendance history with student and subject details
    history = db.session.query(
        Attendance.date,
        Attendance.status,
        Subject.name.label('subject'),
        Section.name.label('section'),
        func.concat(Student.first_name, ' ', Student.last_name).label('student_name'),
        func.count(Attendance.id).label('total_students')
    ).join(Student, Attendance.student_id == Student.id)\
     .join(Subject, Attendance.subject_id == Subject.id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Attendance.instructor_id == instructor_id)\
     .group_by(Attendance.date, Subject.name, Section.name)\
     .order_by(Attendance.date.desc())\
     .limit(50)\
     .all()
    
    return render_template('instructor/attendance_history.html', history=history)

@attendance_bp.route('/attendance/stats', methods=['GET'])
def attendance_stats():
    """Get attendance statistics for instructor dashboard"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    today = date.today()
    
    # Today's classes count
    todays_schedules = InstructorSchedule.query.filter_by(
        instructor_id=instructor_id,
        day=today.strftime('%A')
    ).count()
    
    # Attendance submitted today
    todays_attendance = db.session.query(func.distinct(Attendance.subject_id))\
        .filter(Attendance.instructor_id == instructor_id)\
        .filter(Attendance.date == today)\
        .count()
    
    # Total students under instructor
    total_students = db.session.query(func.count(func.distinct(Student.id)))\
        .join(InstructorSchedule, Student.section_id == InstructorSchedule.section_id)\
        .filter(InstructorSchedule.instructor_id == instructor_id)\
        .scalar()
    
    return jsonify({
        'todays_classes': todays_schedules,
        'attendance_submitted': todays_attendance,
        'total_students': total_students
    })
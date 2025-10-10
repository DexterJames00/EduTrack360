from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import Attendance, Student, Subject, InstructorSchedule, Section, Instructor
from datetime import datetime, date
from sqlalchemy import func
from telegram_bot import send_attendance_notification

attendance_bp = Blueprint('instructor_attendance', __name__)

@attendance_bp.route('/test-ajax', methods=['POST'])
def test_ajax():
    """Test endpoint for AJAX detection"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
             'application/json' in request.headers.get('Accept', '') or \
             request.is_json
    
    return jsonify({
        'success': True,
        'is_ajax': is_ajax,
        'headers': dict(request.headers),
        'message': 'AJAX test successful'
    })

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
        InstructorSchedule.start_time,
        InstructorSchedule.end_time,
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
        InstructorSchedule.start_time,
        InstructorSchedule.end_time,
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
            # Check if this is an AJAX request
            is_ajax = request.args.get('ajax') == '1' or \
                     request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                     'application/json' in request.headers.get('Accept', '') or \
                     request.is_json
            
            print(f"DEBUG: AJAX request detected: {is_ajax}")
            print(f"DEBUG: Form data: {dict(request.form)}")
            
            attendance_date = request.form.get('date')
            if not attendance_date:
                error_msg = 'Please select a date'
                print(f"DEBUG: Date validation failed: {error_msg}")
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            try:
                attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            except ValueError:
                error_msg = 'Invalid date format'
                print(f"DEBUG: Date parsing failed: {error_msg}")
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            # Check if attendance already exists for this date
            existing_attendance = Attendance.query.filter_by(
                date=attendance_date,
                subject_id=schedule.subject_id,
                instructor_id=instructor_id
            ).first()
            
            if existing_attendance:
                error_msg = f'Attendance for {attendance_date.strftime("%B %d, %Y")} has already been recorded for this class. Please choose a different date or contact your administrator to modify existing records.'
                print(f"DEBUG: Duplicate attendance: {error_msg}")
                if is_ajax:
                    return jsonify({
                        'success': False, 
                        'error': error_msg,
                        'duplicate': True,
                        'existing_date': attendance_date.strftime('%Y-%m-%d')
                    }), 400
                flash(error_msg, 'warning')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            # Process attendance for each student
            attendance_records = []
            
            for student in students:
                status = request.form.get(f'status_{student.id}', 'Present')  # Default to Present
                
                # Validate status
                if status not in ['Present', 'Absent', 'Late', 'Excused']:
                    print(f"DEBUG: Invalid status '{status}' for student {student.name}, defaulting to Present")
                    status = 'Present'
                
                attendance_record = Attendance(
                    student_id=student.id,
                    date=attendance_date,
                    status=status,
                    subject_id=schedule.subject_id,
                    instructor_id=instructor_id
                )
                attendance_records.append(attendance_record)
            
            if not attendance_records:
                error_msg = 'No students found in this section'
                print(f"DEBUG: No students: {error_msg}")
                if is_ajax:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('instructor/record_attendance.html', schedule=schedule, students=students)
            
            # Save all attendance records
            db.session.add_all(attendance_records)
            db.session.commit()
            
            # Send Telegram notifications to students
            school_id = session.get('school_id')
            subject = Subject.query.get(schedule.subject_id)
            
            notification_count = 0
            students_with_telegram = 0
            students_without_telegram = 0
            failed_notifications = 0
            students_without_chat_list = []
            
            for record in attendance_records:
                try:
                    # Check if student has telegram_chat_id
                    student = Student.query.get(record.student_id)
                    if student and student.telegram_chat_id:
                        students_with_telegram += 1
                        success = send_attendance_notification(
                            student_id=record.student_id,
                            subject_name=subject.name if subject else 'Unknown Subject',
                            date=attendance_date.strftime('%Y-%m-%d'),
                            status=record.status,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            school_id=school_id
                        )
                        if success:
                            notification_count += 1
                        else:
                            failed_notifications += 1
                    else:
                        students_without_telegram += 1
                        if student:
                            students_without_chat_list.append(f"{student.first_name} {student.last_name}")
                        else:
                            students_without_chat_list.append(f"Student ID {record.student_id}")
                        
                except Exception as e:
                    failed_notifications += 1
                    print(f"Failed to send notification to student {record.student_id}: {str(e)}")
            
            # Create detailed success message
            success_message = f'Attendance recorded successfully for {len(attendance_records)} students'
            if notification_count > 0:
                success_message += f' and {notification_count} Telegram notifications sent'
            if students_without_telegram > 0:
                success_message += f' ({students_without_telegram} students without Telegram)'
            
            # Return JSON response for AJAX requests
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': success_message,
                    'students_recorded': len(attendance_records),
                    'notifications_sent': notification_count,
                    'students_with_telegram': students_with_telegram,
                    'students_without_telegram': students_without_telegram,
                    'failed_notifications': failed_notifications,
                    'students_without_chat_list': students_without_chat_list,
                    'date': attendance_date.strftime('%Y-%m-%d')
                })
            
            flash(success_message, 'success')
            return redirect(url_for('instructor_attendance.attendance_schedule_list'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error recording attendance: {str(e)}'
            print(f"Attendance error: {error_msg}")  # Debug log
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
    
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
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import Attendance, Student, Subject, InstructorSchedule, Section, Instructor
from datetime import datetime, date
from sqlalchemy import func, case
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
    
    # Get attendance history with detailed statistics, organized by subject
    history_query = db.session.query(
        Attendance.date,
        Subject.name.label('subject'),
        Section.name.label('section'),
        func.count(Attendance.id).label('total_students'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == 'Absent', 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == 'Late', 1), else_=0)).label('late_count'),
        func.sum(case((Attendance.status == 'Excused', 1), else_=0)).label('excused_count')
    ).join(Student, Attendance.student_id == Student.id)\
     .join(Subject, Attendance.subject_id == Subject.id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Attendance.instructor_id == instructor_id)\
     .group_by(Attendance.date, Subject.name, Section.name)\
     .order_by(Subject.name, Attendance.date.desc())\
     .limit(100)\
     .all()
    
    # Organize data by subject for cleaner display
    subjects_data = {}
    for record in history_query:
        subject_name = record.subject
        if subject_name not in subjects_data:
            subjects_data[subject_name] = {
                'subject': subject_name,
                'records': [],
                'total_classes': 0,
                'total_students': 0,
                'total_present': 0,
                'total_absent': 0,
                'overall_rate': 0
            }
        
        total = int(record.total_students or 0)
        present = int(record.present_count or 0)
        late = int(record.late_count or 0)
        excused = int(record.excused_count or 0)
        
        # Calculate attendance rate (Present + Late + Excused considered as attended)
        attended = present + late + excused
        attendance_rate = float(attended / total * 100) if total > 0 else 0.0
        
        record_data = {
            'date': record.date,
            'subject': record.subject,
            'section': record.section,
            'total_students': total,
            'present_count': present,
            'absent_count': record.absent_count or 0,
            'late_count': late,
            'excused_count': excused,
            'attendance_rate': round(attendance_rate, 1)
        }
        
        subjects_data[subject_name]['records'].append(record_data)
        subjects_data[subject_name]['total_classes'] += 1
        subjects_data[subject_name]['total_students'] += total
        subjects_data[subject_name]['total_present'] += present
        subjects_data[subject_name]['total_absent'] += int(record.absent_count or 0)
    
    # Calculate overall rates for each subject
    for subject_name, subject_data in subjects_data.items():
        if subject_data['total_students'] > 0:
            subject_data['overall_rate'] = round(
                float(subject_data['total_present'] / subject_data['total_students'] * 100), 1
            )
    
    return render_template('instructor/attendance_history.html', subjects_data=subjects_data)

@attendance_bp.route('/attendance/monthly-report', methods=['GET'])
def monthly_report():
    """View monthly attendance report for instructor"""
    if 'instructor_id' not in session:
        flash('Please log in as an instructor', 'error')
        return redirect(url_for('auth.login'))
    
    instructor_id = session['instructor_id']
    
    # Get month and year from query params, default to current month
    from datetime import datetime
    now = datetime.now()
    month = int(request.args.get('month', now.month))
    year = int(request.args.get('year', now.year))
    
    # Get monthly attendance data, organized by subject
    monthly_data = db.session.query(
        Student.id,
        func.concat(Student.first_name, ' ', Student.last_name).label('student_name'),
        Subject.name.label('subject'),
        Section.name.label('section'),
        func.count(Attendance.id).label('total_classes'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present_count'),
        func.sum(case((Attendance.status == 'Absent', 1), else_=0)).label('absent_count'),
        func.sum(case((Attendance.status == 'Late', 1), else_=0)).label('late_count'),
        func.sum(case((Attendance.status == 'Excused', 1), else_=0)).label('excused_count')
    ).join(Student, Attendance.student_id == Student.id)\
     .join(Subject, Attendance.subject_id == Subject.id)\
     .join(Section, Student.section_id == Section.id)\
     .filter(Attendance.instructor_id == instructor_id)\
     .filter(func.extract('month', Attendance.date) == month)\
     .filter(func.extract('year', Attendance.date) == year)\
     .group_by(Student.id, Student.first_name, Student.last_name, Subject.name, Section.name)\
     .order_by(Subject.name, Section.name, Student.first_name, Student.last_name)\
     .all()
    
    # Organize data by subject for cleaner display
    subjects_data = {}
    for record in monthly_data:
        subject_name = record.subject
        if subject_name not in subjects_data:
            subjects_data[subject_name] = {
                'subject': subject_name,
                'students': [],
                'total_students': 0,
                'excellent_count': 0,
                'good_count': 0,
                'needs_improvement_count': 0,
                'poor_count': 0,
                'average_rate': 0
            }
        
        total = int(record.total_classes or 0)
        present = int(record.present_count or 0)
        late = int(record.late_count or 0)
        excused = int(record.excused_count or 0)
        
        # Calculate attendance rate (Present + Late + Excused considered as attended)
        attended = present + late + excused
        attendance_rate = float(attended / total * 100) if total > 0 else 0.0
        
        # Determine performance status
        if attendance_rate >= 95:
            status = 'Excellent'
            subjects_data[subject_name]['excellent_count'] += 1
        elif attendance_rate >= 85:
            status = 'Good'
            subjects_data[subject_name]['good_count'] += 1
        elif attendance_rate >= 75:
            status = 'Needs Improvement'
            subjects_data[subject_name]['needs_improvement_count'] += 1
        else:
            status = 'Poor'
            subjects_data[subject_name]['poor_count'] += 1
        
        student_data = {
            'student_id': record.id,
            'student_name': record.student_name,
            'section': record.section,
            'total_classes': total,
            'present_count': present,
            'absent_count': record.absent_count or 0,
            'late_count': late,
            'excused_count': excused,
            'attendance_rate': round(attendance_rate, 1),
            'status': status
        }
        
        subjects_data[subject_name]['students'].append(student_data)
        subjects_data[subject_name]['total_students'] += 1
    
    # Calculate average rates for each subject
    for subject_name, subject_data in subjects_data.items():
        if subject_data['students']:
            total_rate = sum(float(student['attendance_rate']) for student in subject_data['students'])
            subject_data['average_rate'] = round(total_rate / len(subject_data['students']), 1)
    
    # Generate month name for display
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = month_names[month] if 1 <= month <= 12 else 'Unknown'
    
    return render_template('instructor/monthly_report.html', 
                         subjects_data=subjects_data,
                         month=month,
                         year=year,
                         month_name=month_name)

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
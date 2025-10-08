from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from database import db
from models import Student, Section
import random, string

school_admin_bp = Blueprint('crud_student', __name__, url_prefix='/school_admin')

# --- Helper to generate a unique code ---
def generate_unique_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        existing = Student.query.filter_by(code=code).first()
        if not existing:
            return code

# --- Show all Students ---
@school_admin_bp.route('/students', methods=['GET'])
def students_page():
    school_id = session.get('school_id')
    if not school_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))  # adjust route name if different

    students = Student.query.filter_by(school_id=school_id).all()
    sections = Section.query.filter_by(school_id=school_id).all()
    return render_template('school_admin/school_admin_students.html', students=students, sections=sections)

# --- Add Student ---
@school_admin_bp.route('/add_student', methods=['POST'])
def add_student():
    school_id = session.get('school_id')
    if not school_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))

    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        grade_level = request.form['grade_level']
        section_id = request.form['section_id']
        parent_contact = request.form['parent_contact']

        # Auto-generate unique code
        code = generate_unique_code()

        new_student = Student(
            first_name=first_name,
            last_name=last_name,
            grade_level=grade_level,
            section_id=section_id,
            parent_contact=parent_contact,
            school_id=school_id,
            code=code
            # telegram_chat_id and telegram_status will use their default values
        )

        db.session.add(new_student)
        db.session.commit()

        # Get section name for response
        section = Section.query.get(section_id)
        section_name = section.name if section else 'No Section'

        success_message = f"Student {first_name} {last_name} added successfully with code {code}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': success_message,
                'student': {
                    'id': new_student.id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'grade_level': grade_level,
                    'section_id': section_id,
                    'section_name': section_name,
                    'parent_contact': parent_contact,
                    'code': code,
                    'telegram_chat_id': new_student.telegram_chat_id,
                    'telegram_status': new_student.telegram_status
                }
            })
        
        flash(success_message, "success")
        return redirect(url_for('crud_student.students_page'))

    except Exception as e:
        db.session.rollback()
        error_message = f"Error adding student: {e}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message}), 500
            
        flash(error_message, "danger")
        return redirect(url_for('crud_student.students_page'))

# --- Edit Student ---
@school_admin_bp.route('/edit_student/<int:student_id>', methods=['POST'])
def edit_student(student_id):
    school_id = session.get('school_id')
    if not school_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))

    try:
        student = Student.query.filter_by(id=student_id, school_id=school_id).first()
        if not student:
            error_message = "Student not found."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_message}), 404
            flash(error_message, "danger")
            return redirect(url_for('crud_student.students_page'))

        student.first_name = request.form['first_name']
        student.last_name = request.form['last_name']
        student.grade_level = request.form['grade_level']
        student.section_id = request.form['section_id']
        student.parent_contact = request.form['parent_contact']

        db.session.commit()

        # Get section name for response
        section = Section.query.get(student.section_id)
        section_name = section.name if section else 'No Section'

        success_message = f"Student {student.first_name} {student.last_name} updated successfully"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': success_message,
                'student': {
                    'id': student.id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'grade_level': student.grade_level,
                    'section_id': student.section_id,
                    'section_name': section_name,
                    'parent_contact': student.parent_contact,
                    'code': student.code,
                    'telegram_chat_id': student.telegram_chat_id,
                    'telegram_status': student.telegram_status
                }
            })
        
        flash(success_message, "success")
        return redirect(url_for('crud_student.students_page'))

    except Exception as e:
        db.session.rollback()
        error_message = f"Error updating student: {e}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message}), 500
            
        flash(error_message, "danger")
        return redirect(url_for('crud_student.students_page'))

# --- Delete Student ---
@school_admin_bp.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    school_id = session.get('school_id')
    if not school_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))

    try:
        student = Student.query.filter_by(id=student_id, school_id=school_id).first()
        if not student:
            error_message = "Student not found."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_message}), 404
            flash(error_message, "danger")
            return redirect(url_for('crud_student.students_page'))

        student_name = f"{student.first_name} {student.last_name}"
        db.session.delete(student)
        db.session.commit()
        
        success_message = f"Student {student_name} deleted successfully"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': success_message,
                'student_id': student_id
            })
        
        flash(success_message, "success")
        return redirect(url_for('crud_student.students_page'))

    except Exception as e:
        db.session.rollback()
        error_message = f"Error deleting student: {e}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message}), 500
            
        flash(error_message, "danger")
        return redirect(url_for('crud_student.students_page'))

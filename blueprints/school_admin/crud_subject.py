from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import Subject, Instructor, Section, SchoolAdmin
import re

subjects_bp = Blueprint('subjects', __name__, url_prefix='/school_admin')

# Get all subjects for the school
@subjects_bp.route('/subjects', methods=['GET'])
def get_subjects():
    # Get school_id from session
    if 'school_id' not in session:
        return render_template('school_admin/school_admin_subjects.html', subjects=[], instructors=[], sections=[])
    
    school_id = session['school_id']
    subjects = Subject.query.filter_by(school_id=school_id).all()
    instructors = Instructor.query.filter_by(school_id=school_id).all()
    sections = Section.query.filter_by(school_id=school_id).all()
    
    # Add creator name to each subject
    for subject in subjects:
        # Find instructors teaching this subject (for display purposes)
        subject.instructor_names = []
        # This would need to be implemented based on your schedule system
        # For now, we'll leave it empty or add sample data
    
    return render_template('school_admin/school_admin_subjects.html', 
                         subjects=subjects, instructors=instructors, sections=sections)

# Create new subject
@subjects_bp.route('/subjects', methods=['POST'])
def create_subject():
    if 'school_id' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        return jsonify({'success': False, 'message': 'Session expired'}), 401

    try:
        school_id = session['school_id']
        name = request.form.get('name', '').strip()
        grade_level = request.form.get('grade_level', '').strip()
        
        # Validation
        if not name:
            return jsonify({'success': False, 'message': 'Subject name is required.'}), 400
            
        if not grade_level:
            return jsonify({'success': False, 'message': 'Grade level is required.'}), 400
        
        # Check for duplicate subject names in the same school and grade level
        existing_subject = Subject.query.filter_by(
            school_id=school_id, 
            name=name, 
            grade_level=grade_level
        ).first()
        
        if existing_subject:
            return jsonify({
                'success': False, 
                'message': f'Subject "{name}" already exists for grade level "{grade_level}".'
            }), 400

        # Create new subject
        new_subject = Subject(
            name=name,
            grade_level=grade_level,
            school_id=school_id
        )
        
        db.session.add(new_subject)
        db.session.commit()
        
        # Return the new subject data
        subject_data = {
            'id': new_subject.id,
            'name': new_subject.name,
            'grade_level': new_subject.grade_level,
            'school_id': new_subject.school_id
        }
        
        return jsonify({
            'success': True, 
            'message': f'Subject "{name}" created successfully!',
            'subject': subject_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error creating subject: {str(e)}'
        }), 500

# Update subject
@subjects_bp.route('/subjects/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    if 'school_id' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        return jsonify({'success': False, 'message': 'Session expired'}), 401

    try:
        school_id = session['school_id']
        subject = Subject.query.filter_by(id=subject_id, school_id=school_id).first()
        
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found.'}), 404
        
        name = request.form.get('name', '').strip()
        grade_level = request.form.get('grade_level', '').strip()
        
        # Validation
        if not name:
            return jsonify({'success': False, 'message': 'Subject name is required.'}), 400
            
        if not grade_level:
            return jsonify({'success': False, 'message': 'Grade level is required.'}), 400
        
        # Check for duplicate subject names (excluding current subject)
        existing_subject = Subject.query.filter_by(
            school_id=school_id, 
            name=name, 
            grade_level=grade_level
        ).filter(Subject.id != subject_id).first()
        
        if existing_subject:
            return jsonify({
                'success': False, 
                'message': f'Subject "{name}" already exists for grade level "{grade_level}".'
            }), 400

        # Update subject
        subject.name = name
        subject.grade_level = grade_level
        
        db.session.commit()
        
        # Return updated subject data
        subject_data = {
            'id': subject.id,
            'name': subject.name,
            'grade_level': subject.grade_level,
            'school_id': subject.school_id
        }
        
        return jsonify({
            'success': True, 
            'message': f'Subject "{name}" updated successfully!',
            'subject': subject_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error updating subject: {str(e)}'
        }), 500

# Delete subject
@subjects_bp.route('/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    if 'school_id' not in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        return jsonify({'success': False, 'message': 'Session expired'}), 401

    try:
        school_id = session['school_id']
        subject = Subject.query.filter_by(id=subject_id, school_id=school_id).first()
        
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found.'}), 404
        
        subject_name = subject.name
        
        # Check if subject has any related records (schedules, attendance)
        # You might want to add checks here for related data
        
        db.session.delete(subject)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Subject "{subject_name}" deleted successfully!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error deleting subject: {str(e)}'
        }), 500

@subjects_bp.route('/subjects/api', methods=['GET'])
def get_subjects_api():
    """API endpoint to get all subjects for dropdown"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    school_id = session['school_id']
    
    try:
        subjects = Subject.query.filter_by(school_id=school_id).all()
        
        subjects_list = []
        for subject in subjects:
            subjects_list.append({
                'id': subject.id,
                'name': subject.name,
                'grade_level': subject.grade_level
            })
        
        return jsonify({'subjects': subjects_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

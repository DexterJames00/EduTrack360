from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from database import db
from models import Instructor, Subject, Section, InstructorSchedule, SchoolAdmin
from sqlalchemy import func
import hashlib
from datetime import datetime

assignment_bp = Blueprint('instructor_assignment', __name__, url_prefix='/school_admin')

@assignment_bp.route('/assignments', methods=['POST'])
def create_assignment():
    """Create a new instructor assignment"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    try:
        data = request.get_json()
        instructor_id = data.get('instructor_id')
        subject_id = data.get('subject_id')
        section_id = data.get('section_id')
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # Normalize day and time inputs
        VALID_DAYS = {'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'}

        def normalize_time(value: str | None) -> str | None:
            if not value:
                return None
            v = value.strip()
            # Try 24h first (HH:MM)
            for fmt in ('%H:%M', '%H:%M:%S'):
                try:
                    return datetime.strptime(v, fmt).strftime('%H:%M')
                except Exception:
                    pass
            # Try 12h with AM/PM
            v_up = v.upper().replace('.', '')
            for fmt in ('%I:%M %p', '%I:%M%p'):
                try:
                    return datetime.strptime(v_up, fmt).strftime('%H:%M')
                except Exception:
                    pass
            return None
        
        # Validate required fields
        if not all([instructor_id, subject_id, section_id, day, start_time, end_time]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        # Validate day
        if day not in VALID_DAYS:
            return jsonify({'success': False, 'message': 'Invalid day provided'}), 400

        # Normalize times
        n_start = normalize_time(start_time)
        n_end = normalize_time(end_time)
        if not n_start or not n_end:
            return jsonify({'success': False, 'message': 'Invalid time format. Use HH:MM or h:MM AM/PM'}), 400

        # Validate time range
        if n_start >= n_end:
            return jsonify({
                'success': False,
                'message': 'End time must be after start time'
            }), 400
        
        # Verify instructor belongs to the school
        instructor = Instructor.query.filter_by(
            id=instructor_id, 
            school_id=session['school_id']
        ).first()
        
        if not instructor:
            return jsonify({
                'success': False,
                'message': 'Instructor not found'
            }), 404
        
        # Verify subject belongs to the school
        subject = Subject.query.filter_by(
            id=subject_id,
            school_id=session['school_id']
        ).first()
        
        if not subject:
            return jsonify({
                'success': False,
                'message': 'Subject not found'
            }), 404
        
        # Verify section belongs to the school
        section = Section.query.filter_by(
            id=section_id,
            school_id=session['school_id']
        ).first()
        
        if not section:
            return jsonify({
                'success': False,
                'message': 'Section not found'
            }), 404
        
        # Check for duplicate assignments
        existing_assignment = InstructorSchedule.query.filter_by(
            instructor_id=instructor_id,
            subject_id=subject_id,
            section_id=section_id,
            day=day
        ).first()
        
        if existing_assignment:
            return jsonify({
                'success': False,
                'message': f'Assignment already exists for {instructor.name} teaching {subject.name} to {section.grade_level}-{section.name} on {day}'
            }), 400
        
        # Check for section time conflicts (same section can't have two classes at the same time)
        section_conflicts = InstructorSchedule.query.filter(
            InstructorSchedule.section_id == section_id,
            InstructorSchedule.day == day,
            InstructorSchedule.start_time < n_end,
            InstructorSchedule.end_time > n_start
        ).first()
        
        if section_conflicts:
            conflict_subject = Subject.query.get(section_conflicts.subject_id)
            conflict_subject_name = conflict_subject.name if conflict_subject else 'another subject'
            return jsonify({
                'success': False,
                'message': f'Time conflict! {section.grade_level}-{section.name} already has {conflict_subject_name} scheduled on {day} from {section_conflicts.start_time} to {section_conflicts.end_time}'
            }), 400
        
        # Check for instructor time conflicts (same instructor can't teach two classes at the same time)
        instructor_conflicts = InstructorSchedule.query.filter(
            InstructorSchedule.instructor_id == instructor_id,
            InstructorSchedule.day == day,
            InstructorSchedule.start_time < n_end,
            InstructorSchedule.end_time > n_start
        ).first()
        
        if instructor_conflicts:
            conflict_subject = Subject.query.get(instructor_conflicts.subject_id)
            conflict_section = Section.query.get(instructor_conflicts.section_id)
            conflict_subject_name = conflict_subject.name if conflict_subject else 'another subject'
            conflict_section_name = f"{conflict_section.grade_level}-{conflict_section.name}" if conflict_section else 'another section'
            return jsonify({
                'success': False,
                'message': f'Time conflict! {instructor.name} is already teaching {conflict_subject_name} to {conflict_section_name} on {day} from {instructor_conflicts.start_time} to {instructor_conflicts.end_time}'
            }), 400
        
        # Create new assignment
        new_assignment = InstructorSchedule(
            instructor_id=instructor_id,
            subject_id=subject_id,
            section_id=section_id,
            day=day,
            start_time=n_start,
            end_time=n_end
        )
        
        db.session.add(new_assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Assignment created successfully!'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating assignment: {str(e)}'
        }), 500

@assignment_bp.route('/assignments/instructor/<int:instructor_id>', methods=['GET'])
def get_instructor_assignments(instructor_id):
    """Get all assignments for a specific instructor"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    school_id = session['school_id']
    
    assignments = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.start_time,
        InstructorSchedule.end_time,
        InstructorSchedule.day,
        Subject.name.label('subject_name'),
        Subject.name.label('subject_code'),
        Section.name.label('section_name'),
        Section.grade_level
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
     .filter(Instructor.school_id == school_id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .order_by(InstructorSchedule.day, InstructorSchedule.start_time)\
     .all()
    
    assignment_list = []
    for assignment in assignments:
        assignment_list.append({
            'id': assignment.id,
            'start_time': assignment.start_time,
            'end_time': assignment.end_time,
            'day': assignment.day,
            'subject_name': assignment.subject_name,
            'subject_code': assignment.subject_code,
            'section_name': assignment.section_name,
            'grade_level': assignment.grade_level
        })
    
    return jsonify({'assignments': assignment_list})

@assignment_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """Delete an assignment"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    try:
        assignment = db.session.query(InstructorSchedule)\
            .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
            .filter(InstructorSchedule.id == assignment_id)\
            .filter(Instructor.school_id == session['school_id'])\
            .first()
        
        if not assignment:
            return jsonify({
                'success': False,
                'message': 'Assignment not found'
            }), 404
        
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Assignment deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting assignment: {str(e)}'
        }), 500

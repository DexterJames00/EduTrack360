from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
from database import db
from models import Instructor, Subject, Section, InstructorSchedule, SchoolAdmin
from sqlalchemy import func

assignment_bp = Blueprint('instructor_assignment', __name__, url_prefix='/school_admin')

@assignment_bp.route('/assignments', methods=['GET'])
def view_assignments():
    """View all instructor assignments"""
    if 'school_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('auth.login'))
    
    school_id = session['school_id']
    
    # Get all assignments with instructor, subject, and section details
    assignments = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        InstructorSchedule.day,
        Instructor.name.label('instructor_name'),
        Instructor.id.label('instructor_id'),
        Subject.name.label('subject_name'),
        Subject.id.label('subject_id'),
        Subject.grade_level.label('subject_grade'),
        Section.name.label('section_name'),
        Section.id.label('section_id'),
        Section.grade_level.label('section_grade')
    ).join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
     .join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(Instructor.school_id == school_id)\
     .order_by(InstructorSchedule.day, InstructorSchedule.time, Instructor.name)\
     .all()
    
    # Get available instructors, subjects, and sections for the form
    instructors = Instructor.query.filter_by(school_id=school_id).all()
    subjects = Subject.query.filter_by(school_id=school_id).all()
    sections = Section.query.filter_by(school_id=school_id).all()
    
    # Organize assignments by day for better visualization
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    organized_assignments = {day: [] for day in days}
    
    for assignment in assignments:
        if assignment.day in organized_assignments:
            organized_assignments[assignment.day].append(assignment)
    
    return render_template(
        'school_admin/instructor_assignments.html',
        assignments=assignments,
        organized_assignments=organized_assignments,
        instructors=instructors,
        subjects=subjects,
        sections=sections,
        days=days
    )

@assignment_bp.route('/assignments/create', methods=['POST'])
def create_assignment():
    """Create new instructor assignment"""
    try:
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired'}), 401
        
        school_id = session['school_id']
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['instructor_id', 'subject_id', 'section_id', 'time', 'day']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        instructor_id = data['instructor_id']
        subject_id = data['subject_id']
        section_id = data['section_id']
        time = data['time']
        day = data['day']
        
        # Verify instructor belongs to school
        instructor = Instructor.query.filter_by(id=instructor_id, school_id=school_id).first()
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found'}), 404
        
        # Verify subject belongs to school
        subject = Subject.query.filter_by(id=subject_id, school_id=school_id).first()
        if not subject:
            return jsonify({'success': False, 'message': 'Subject not found'}), 404
        
        # Verify section belongs to school
        section = Section.query.filter_by(id=section_id, school_id=school_id).first()
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'}), 404
        
        # Check for conflicts - instructor already has class at this time/day
        instructor_conflict = InstructorSchedule.query.join(Instructor)\
            .filter(Instructor.school_id == school_id)\
            .filter(InstructorSchedule.instructor_id == instructor_id)\
            .filter(InstructorSchedule.day == day)\
            .filter(InstructorSchedule.time == time)\
            .first()
        
        if instructor_conflict:
            return jsonify({
                'success': False, 
                'message': f'Instructor {instructor.name} already has a class at {time} on {day}'
            }), 400
        
        # Check for conflicts - section already has class at this time/day
        section_conflict = InstructorSchedule.query.join(Section)\
            .filter(Section.school_id == school_id)\
            .filter(InstructorSchedule.section_id == section_id)\
            .filter(InstructorSchedule.day == day)\
            .filter(InstructorSchedule.time == time)\
            .first()
        
        if section_conflict:
            return jsonify({
                'success': False, 
                'message': f'Section {section.name} already has a class at {time} on {day}'
            }), 400
        
        # Create the assignment
        assignment = InstructorSchedule(
            instructor_id=instructor_id,
            subject_id=subject_id,
            section_id=section_id,
            time=time,
            day=day
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Assignment created successfully!',
            'assignment': {
                'id': assignment.id,
                'instructor_name': instructor.name,
                'subject_name': subject.name,
                'section_name': section.name,
                'time': time,
                'day': day
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating assignment: {str(e)}'}), 500

@assignment_bp.route('/assignments/update/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """Update instructor assignment"""
    try:
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired'}), 401
        
        school_id = session['school_id']
        data = request.get_json()
        
        # Find the assignment
        assignment = db.session.query(InstructorSchedule)\
            .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
            .filter(Instructor.school_id == school_id)\
            .filter(InstructorSchedule.id == assignment_id)\
            .first()
        
        if not assignment:
            return jsonify({'success': False, 'message': 'Assignment not found'}), 404
        
        # Validate required fields
        required_fields = ['instructor_id', 'subject_id', 'section_id', 'time', 'day']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        instructor_id = data['instructor_id']
        subject_id = data['subject_id']
        section_id = data['section_id']
        time = data['time']
        day = data['day']
        
        # Verify all entities belong to school
        instructor = Instructor.query.filter_by(id=instructor_id, school_id=school_id).first()
        subject = Subject.query.filter_by(id=subject_id, school_id=school_id).first()
        section = Section.query.filter_by(id=section_id, school_id=school_id).first()
        
        if not instructor or not subject or not section:
            return jsonify({'success': False, 'message': 'Invalid instructor, subject, or section'}), 400
        
        # Check for conflicts (excluding current assignment)
        instructor_conflict = InstructorSchedule.query.join(Instructor)\
            .filter(Instructor.school_id == school_id)\
            .filter(InstructorSchedule.instructor_id == instructor_id)\
            .filter(InstructorSchedule.day == day)\
            .filter(InstructorSchedule.time == time)\
            .filter(InstructorSchedule.id != assignment_id)\
            .first()
        
        if instructor_conflict:
            return jsonify({
                'success': False, 
                'message': f'Instructor {instructor.name} already has a class at {time} on {day}'
            }), 400
        
        section_conflict = InstructorSchedule.query.join(Section)\
            .filter(Section.school_id == school_id)\
            .filter(InstructorSchedule.section_id == section_id)\
            .filter(InstructorSchedule.day == day)\
            .filter(InstructorSchedule.time == time)\
            .filter(InstructorSchedule.id != assignment_id)\
            .first()
        
        if section_conflict:
            return jsonify({
                'success': False, 
                'message': f'Section {section.name} already has a class at {time} on {day}'
            }), 400
        
        # Update the assignment
        assignment.instructor_id = instructor_id
        assignment.subject_id = subject_id
        assignment.section_id = section_id
        assignment.time = time
        assignment.day = day
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Assignment updated successfully!',
            'assignment': {
                'id': assignment.id,
                'instructor_name': instructor.name,
                'subject_name': subject.name,
                'section_name': section.name,
                'time': time,
                'day': day
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating assignment: {str(e)}'}), 500

@assignment_bp.route('/assignments/delete/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """Delete instructor assignment"""
    try:
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired'}), 401
        
        school_id = session['school_id']
        
        # Find the assignment
        assignment = db.session.query(InstructorSchedule)\
            .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
            .filter(Instructor.school_id == school_id)\
            .filter(InstructorSchedule.id == assignment_id)\
            .first()
        
        if not assignment:
            return jsonify({'success': False, 'message': 'Assignment not found'}), 404
        
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Assignment deleted successfully!',
            'assignment_id': assignment_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting assignment: {str(e)}'}), 500

@assignment_bp.route('/assignments/instructor/<int:instructor_id>', methods=['GET'])
def get_instructor_assignments(instructor_id):
    """Get all assignments for a specific instructor"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    school_id = session['school_id']
    
    assignments = db.session.query(
        InstructorSchedule.id,
        InstructorSchedule.time,
        InstructorSchedule.day,
        Subject.name.label('subject_name'),
        Section.name.label('section_name'),
        Section.grade_level
    ).join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
     .filter(Instructor.school_id == school_id)\
     .filter(InstructorSchedule.instructor_id == instructor_id)\
     .order_by(InstructorSchedule.day, InstructorSchedule.time)\
     .all()
    
    assignment_list = []
    for assignment in assignments:
        assignment_list.append({
            'id': assignment.id,
            'time': assignment.time,
            'day': assignment.day,
            'subject_name': assignment.subject_name,
            'section_name': assignment.section_name,
            'grade_level': assignment.grade_level
        })
    
    return jsonify({'assignments': assignment_list})

@assignment_bp.route('/assignments/conflicts', methods=['GET'])
def check_conflicts():
    """Check for scheduling conflicts"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    school_id = session['school_id']
    
    # Find time slots with multiple assignments
    conflicts = db.session.query(
        InstructorSchedule.day,
        InstructorSchedule.time,
        func.count(InstructorSchedule.id).label('conflict_count'),
        func.group_concat(Instructor.name).label('instructors'),
        func.group_concat(Subject.name).label('subjects'),
        func.group_concat(Section.name).label('sections')
    ).join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
     .join(Subject, InstructorSchedule.subject_id == Subject.id)\
     .join(Section, InstructorSchedule.section_id == Section.id)\
     .filter(Instructor.school_id == school_id)\
     .group_by(InstructorSchedule.day, InstructorSchedule.time)\
     .having(func.count(InstructorSchedule.id) > 1)\
     .all()
    
    conflict_list = []
    for conflict in conflicts:
        conflict_list.append({
            'day': conflict.day,
            'time': conflict.time,
            'count': conflict.conflict_count,
            'instructors': conflict.instructors.split(',') if conflict.instructors else [],
            'subjects': conflict.subjects.split(',') if conflict.subjects else [],
            'sections': conflict.sections.split(',') if conflict.sections else []
        })
    
    return jsonify({'conflicts': conflict_list})

@assignment_bp.route('/assignments/stats', methods=['GET'])
def assignment_stats():
    """Get assignment statistics"""
    if 'school_id' not in session:
        return jsonify({'error': 'Session expired'}), 401
    
    school_id = session['school_id']
    
    # Total assignments
    total_assignments = db.session.query(InstructorSchedule)\
        .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
        .filter(Instructor.school_id == school_id)\
        .count()
    
    # Instructors with assignments
    instructors_with_assignments = db.session.query(func.count(func.distinct(InstructorSchedule.instructor_id)))\
        .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
        .filter(Instructor.school_id == school_id)\
        .scalar()
    
    # Total instructors
    total_instructors = Instructor.query.filter_by(school_id=school_id).count()
    
    # Subjects being taught
    subjects_taught = db.session.query(func.count(func.distinct(InstructorSchedule.subject_id)))\
        .join(Instructor, InstructorSchedule.instructor_id == Instructor.id)\
        .filter(Instructor.school_id == school_id)\
        .scalar()
    
    # Total subjects
    total_subjects = Subject.query.filter_by(school_id=school_id).count()
    
    return jsonify({
        'total_assignments': total_assignments,
        'instructors_with_assignments': instructors_with_assignments,
        'total_instructors': total_instructors,
        'subjects_taught': subjects_taught,
        'total_subjects': total_subjects,
        'instructor_utilization': round((instructors_with_assignments / total_instructors * 100) if total_instructors > 0 else 0, 1),
        'subject_coverage': round((subjects_taught / total_subjects * 100) if total_subjects > 0 else 0, 1)
    })
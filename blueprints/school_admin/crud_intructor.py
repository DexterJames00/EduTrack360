from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import Instructor

school_admin_bp = Blueprint('crud_instructor', __name__, url_prefix='/school_admin')

# Get all instructors for the school
@school_admin_bp.route('/instructors', methods=['GET'])
def get_instructors():
    # Get school_id from session
    if 'school_id' not in session:
        return render_template('school_admin/school_admin_instructors.html', instructors=[])
    
    school_id = session['school_id']
    instructors = Instructor.query.filter_by(school_id=school_id).all()
    
    # Add creator name to each instructor
    for instructor in instructors:
        if instructor.created_by:
            # You might want to fetch the creator's name from SchoolAdmin table
            instructor.creator_name = f"Admin ID: {instructor.created_by}"
        else:
            instructor.creator_name = "Unknown"
    
    return render_template('school_admin/school_admin_instructors.html', instructors=instructors)

@school_admin_bp.route('/create/instructor', methods=['POST'])
def create_instructor():
    try:
        data = request.get_json()
        
        # Get required data from session
        if 'school_id' not in session or 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401
        
        school_id = session['school_id']
        created_by = session['user_id']  # This is the session['user_id'] = user.id
        
        # Validate required fields
        if not data.get('name') or not data.get('gender') or not data.get('email') or not data.get('address'):
            return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

        # Create Instructor object
        new_instructor = Instructor(
            name=data.get('name'),
            gender=data.get('gender'),
            email=data.get('email'),
            address=data.get('address'),
            school_id=school_id,
            created_by=created_by  # Using session['user_id']
        )

        db.session.add(new_instructor)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Instructor created successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to create instructor: {str(e)}'}), 500

# Update instructor
@school_admin_bp.route('/update/instructor/<int:id>', methods=['PUT'])
def update_instructor(id):
    try:
        # Get school_id from session
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401
        
        school_id = session['school_id']
        instructor = Instructor.query.filter_by(id=id, school_id=school_id).first()
        
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found or permission denied.'}), 404
        
        data = request.get_json()
        
        # Update instructor fields
        instructor.name = data.get('name', instructor.name)
        instructor.gender = data.get('gender', instructor.gender)
        instructor.email = data.get('email', instructor.email)
        instructor.address = data.get('address', instructor.address)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Instructor updated successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update instructor: {str(e)}'}), 500

# Delete instructor
@school_admin_bp.route('/delete/instructor/<int:id>', methods=['DELETE'])
def delete_instructor(id):
    try:
        # Get school_id from session
        if 'school_id' not in session:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401
        
        school_id = session['school_id']
        instructor = Instructor.query.filter_by(id=id, school_id=school_id).first()
        
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found or permission denied.'}), 404
        
        db.session.delete(instructor)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Instructor deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete instructor: {str(e)}'}), 500

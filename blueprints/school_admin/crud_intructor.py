from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import Instructor, SchoolAdmin

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
            # Fetch the creator's actual username from SchoolAdmin table
            creator = SchoolAdmin.query.filter_by(id=instructor.created_by).first()
            if creator:
                instructor.creator_name = creator.username
            else:
                instructor.creator_name = "Unknown Admin"
        else:
            instructor.creator_name = "System"
    
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

        # Check for duplicate email in the same school
        existing_instructor_email = Instructor.query.filter_by(
            email=data.get('email').strip().lower(), 
            school_id=school_id
        ).first()
        
        if existing_instructor_email:
            return jsonify({
                'success': False, 
                'message': f'An instructor with email "{data.get("email")}" already exists in your school.'
            }), 400

        # Check for duplicate name in the same school
        existing_instructor_name = Instructor.query.filter_by(
            name=data.get('name').strip(), 
            school_id=school_id
        ).first()
        
        if existing_instructor_name:
            return jsonify({
                'success': False, 
                'message': f'An instructor named "{data.get("name")}" already exists in your school.'
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.get('email').strip()):
            return jsonify({
                'success': False, 
                'message': 'Please enter a valid email address.'
            }), 400

        # Create Instructor object
        new_instructor = Instructor(
            name=data.get('name').strip(),
            gender=data.get('gender'),
            email=data.get('email').strip().lower(),
            address=data.get('address').strip(),
            school_id=school_id,
            created_by=created_by  # Using session['user_id']
        )

        db.session.add(new_instructor)
        db.session.commit()

        # Get creator name for response
        creator = SchoolAdmin.query.filter_by(id=created_by).first()
        creator_name = creator.username if creator else "Admin"

        return jsonify({
            'success': True, 
            'message': 'Instructor created successfully!',
            'instructor': {
                'id': new_instructor.id,
                'name': new_instructor.name,
                'gender': new_instructor.gender,
                'email': new_instructor.email,
                'address': new_instructor.address,
                'creator_name': creator_name
            }
        })
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
        
        # Validate required fields
        if not data.get('name') or not data.get('gender') or not data.get('email') or not data.get('address'):
            return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

        # Check for duplicate email in the same school (excluding current instructor)
        existing_instructor_email = Instructor.query.filter(
            Instructor.email == data.get('email').strip().lower(),
            Instructor.school_id == school_id,
            Instructor.id != id
        ).first()
        
        if existing_instructor_email:
            return jsonify({
                'success': False, 
                'message': f'Another instructor with email "{data.get("email")}" already exists in your school.'
            }), 400

        # Check for duplicate name in the same school (excluding current instructor)
        existing_instructor_name = Instructor.query.filter(
            Instructor.name == data.get('name').strip(),
            Instructor.school_id == school_id,
            Instructor.id != id
        ).first()
        
        if existing_instructor_name:
            return jsonify({
                'success': False, 
                'message': f'Another instructor named "{data.get("name")}" already exists in your school.'
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data.get('email').strip()):
            return jsonify({
                'success': False, 
                'message': 'Please enter a valid email address.'
            }), 400
        
        # Update instructor fields
        instructor.name = data.get('name').strip()
        instructor.gender = data.get('gender')
        instructor.email = data.get('email').strip().lower()
        instructor.address = data.get('address').strip()
        
        db.session.commit()
        
        # Get creator name for response
        creator = SchoolAdmin.query.filter_by(id=instructor.created_by).first()
        creator_name = creator.username if creator else "Admin"
        
        return jsonify({
            'success': True, 
            'message': 'Instructor updated successfully!',
            'instructor': {
                'id': instructor.id,
                'name': instructor.name,
                'gender': instructor.gender,
                'email': instructor.email,
                'address': instructor.address,
                'creator_name': creator_name
            }
        })
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
        return jsonify({
            'success': True, 
            'message': 'Instructor deleted successfully!',
            'instructor_id': id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete instructor: {str(e)}'}), 500

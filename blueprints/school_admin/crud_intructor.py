from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import Instructor, SchoolAdmin
from activity_logger import log_activity

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

        # Log the activity
        log_activity(
            action='CREATE',
            entity_type='instructor',
            entity_id=new_instructor.id,
            entity_name=new_instructor.name,
            description=f"Created new instructor: {new_instructor.name} ({new_instructor.email})"
        )

        # Get creator name for response
        creator = SchoolAdmin.query.filter_by(id=created_by).first()
        creator_name = creator.username if creator else "Admin"

        # Emit real-time update
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                event_data = {
                    'school_id': school_id,
                    'instructor': {
                        'id': new_instructor.id,
                        'name': new_instructor.name,
                        'gender': new_instructor.gender,
                        'email': new_instructor.email,
                        'address': new_instructor.address,
                        'creator_name': creator_name
                    }
                }
                print(f"📢 Emitting instructor_created event: {event_data}")
                current_app.socketio.emit('instructor_created', event_data, room=f'school_{school_id}')
                print(f"✅ Successfully emitted to room: school_{school_id}")
            else:
                print("❌ No socketio found in current_app")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")

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
        
        # Store old values for logging
        old_name = instructor.name
        
        # Update instructor fields
        instructor.name = data.get('name').strip()
        instructor.gender = data.get('gender')
        instructor.email = data.get('email').strip().lower()
        instructor.address = data.get('address').strip()
        
        db.session.commit()

        # Log the activity
        log_activity(
            action='UPDATE',
            entity_type='instructor',
            entity_id=instructor.id,
            entity_name=instructor.name,
            description=f"Updated instructor: {old_name} → {instructor.name} ({instructor.email})"
        )
        
        # Emit real-time update
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                event_data = {
                    'school_id': school_id,
                    'instructor': {
                        'id': instructor.id,
                        'name': instructor.name,
                        'gender': instructor.gender,
                        'email': instructor.email,
                        'address': instructor.address
                    }
                }
                print(f"📢 Emitting instructor_updated event: {event_data}")
                current_app.socketio.emit('instructor_updated', event_data, room=f'school_{school_id}')
                print(f"✅ Successfully emitted to room: school_{school_id}")
            else:
                print("❌ No socketio found in current_app")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")
        
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
        
        # Store instructor info for real-time update before deletion
        instructor_name = instructor.name
        
        # First, delete all related records to avoid foreign key constraint errors
        from models import SchoolInstructorAccount, SectionAdviser, InstructorSchedule, Attendance
        
        # Delete SchoolInstructorAccount records
        school_instructor_accounts = SchoolInstructorAccount.query.filter_by(instructor_id=id).all()
        for account in school_instructor_accounts:
            db.session.delete(account)
        
        # Delete SectionAdviser records
        section_advisers = SectionAdviser.query.filter_by(instructor_id=id).all()
        for adviser in section_advisers:
            db.session.delete(adviser)
        
        # Delete InstructorSchedule records
        schedules = InstructorSchedule.query.filter_by(instructor_id=id).all()
        for schedule in schedules:
            db.session.delete(schedule)
        
        # Delete Attendance records
        attendances = Attendance.query.filter_by(instructor_id=id).all()
        for attendance in attendances:
            db.session.delete(attendance)
        
        # Log the activity before deletion
        log_activity(
            action='DELETE',
            entity_type='instructor',
            entity_id=id,
            entity_name=instructor.name,
            description=f"Deleted instructor: {instructor.name} ({instructor.email}) and all related records"
        )

        # Now we can safely delete the instructor
        db.session.delete(instructor)
        db.session.commit()
        
        # Emit real-time update after successful deletion
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                event_data = {
                    'school_id': school_id,
                    'instructor': {
                        'id': id,
                        'name': instructor_name
                    }
                }
                print(f"📢 Emitting instructor_deleted event: {event_data}")
                current_app.socketio.emit('instructor_deleted', event_data, room=f'school_{school_id}')
                print(f"✅ Successfully emitted to room: school_{school_id}")
            else:
                print("❌ No socketio found in current_app")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")
        
        return jsonify({
            'success': True, 
            'message': 'Instructor deleted successfully!',
            'instructor_id': id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete instructor: {str(e)}'}), 500

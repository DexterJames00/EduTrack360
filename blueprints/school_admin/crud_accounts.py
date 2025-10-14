from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import SchoolAdmin, SchoolInstructorAccount, Instructor
from activity_logger import log_activity
from werkzeug.security import generate_password_hash

school_admin_bp = Blueprint('school_admin_accounts', __name__, url_prefix='/school_admin/accounts')


# -------------------------------
# Render the Accounts Page
# -------------------------------
@school_admin_bp.route('/', methods=['GET'])
def accounts():
    if 'school_id' not in session:
        return render_template('school_admin/accounts.html', accounts=[], instructors=[])
    
    school_id = session['school_id']

    # Fetch school admins and instructor accounts
    school_admins = SchoolAdmin.query.filter_by(school_id=school_id).all()
    instructor_accounts = SchoolInstructorAccount.query.filter_by(school_id=school_id).all()

    all_accounts = []

    # Add school admin accounts
    for admin in school_admins:
        all_accounts.append({
            'id': admin.id,
            'username': admin.username,
            'school_id': admin.school_id,
            'role': admin.role,
            'type': 'school_admin'
        })

    # Add instructor accounts (linked via instructor)
    for inst_acc in instructor_accounts:
        if inst_acc.instructor:
            all_accounts.append({
                'id': inst_acc.id,
                'username': inst_acc.instructor.email,
                'school_id': inst_acc.school_id,
                'role': 'school_instructor',
                'type': 'school_instructor',
                'instructor_name': inst_acc.instructor.name
            })

    # Fetch all instructors for the dropdown
    instructors = Instructor.query.filter_by(school_id=school_id).all()

    return render_template('school_admin/accounts.html', accounts=all_accounts, instructors=instructors)


# -------------------------------
# Create Account
# -------------------------------
@school_admin_bp.route('/create', methods=['POST'])
def create_account():
    data = request.get_json()
    if not data.get('username') or not data.get('password') or not data.get('role'):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    if 'school_id' not in session:
        return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

    school_id = session['school_id']
    school_admin_id = session['user_id']
    hashed_password = generate_password_hash(data['password'])

    try:
        if data['role'] == 'school_admin':
            # Prevent duplicate usernames
            existing_admin = SchoolAdmin.query.filter_by(username=data['username'], school_id=school_id).first()
            if existing_admin:
                return jsonify({"success": False, "message": "This admin account already exists."}), 400

            account = SchoolAdmin(
                username=data['username'],
                password=hashed_password,
                school_id=school_id,
                role=data['role']
            )
            db.session.add(account)

        elif data['role'] == 'school_instructor':
            # Find existing instructor by email
            instructor = Instructor.query.filter_by(email=data['username'], school_id=school_id).first()
            if not instructor:
                return jsonify({"success": False, "message": "Instructor not found for this email."}), 404

            # Prevent duplicate instructor accounts
            existing_account = SchoolInstructorAccount.query.filter_by(instructor_id=instructor.id, school_id=school_id).first()
            if existing_account:
                return jsonify({"success": False, "message": "This instructor already has an account."}), 400

            account = SchoolInstructorAccount(
                instructor_id=instructor.id,
                school_admin_id=school_admin_id,
                school_id=school_id,
                password=hashed_password  # Now we store the password
            )
            db.session.add(account)

        db.session.commit()

        # Log the activity
        log_activity(
            action='CREATE',
            entity_type='account',
            entity_id=account.id,
            entity_name=data['username'],
            description=f"Created new {data['role']} account: {data['username']}"
        )

        # Emit real-time update
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                account_data = {
                    'id': account.id,
                    'username': data['username'],
                    'school_id': school_id,
                    'role': data['role'],
                    'type': data['role']
                }
                
                # Add instructor name if it's an instructor account
                if data['role'] == 'school_instructor' and instructor:
                    account_data['instructor_name'] = instructor.name
                
                current_app.socketio.emit('account_created', {
                    'school_id': school_id,
                    'account': account_data
                }, room=f'school_{school_id}')
                print(f"📢 Emitting account_created event: {{'school_id': {school_id}, 'account': {{'id': {account.id}, 'username': '{data['username']}'}}}}")
                print(f"✅ Successfully emitted to room: school_{school_id}")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")
        
        return jsonify({"success": True, "message": "Account saved successfully!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# Update Account
# -------------------------------
@school_admin_bp.route('/update/<int:id>', methods=['PUT'])
def update_account(id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided."}), 400

    school_id = session.get('school_id')
    if not school_id:
        return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

    try:
        # Try to find in SchoolAdmin first
        account = SchoolAdmin.query.filter_by(id=id, school_id=school_id).first()

        if account:
            account.username = data.get('username', account.username)
            account.role = data.get('role', account.role)
            if data.get('password'):
                account.password = generate_password_hash(data['password'])
        else:
            # Otherwise, check if it's an instructor account
            account = SchoolInstructorAccount.query.filter_by(id=id, school_id=school_id).first()
            if not account:
                return jsonify({"success": False, "message": "Account not found."}), 404

            # Update instructor account password
            if data.get('password'):
                account.password = generate_password_hash(data['password'])
            
            # Update instructor email if provided
            instructor = account.instructor
            if instructor and data.get('username'):
                instructor.email = data['username']

        db.session.commit()

        # Log the activity
        username = data.get('username') if data.get('username') else (account.username if hasattr(account, 'username') else account.instructor.email)
        log_activity(
            action='UPDATE',
            entity_type='account',
            entity_id=id,
            entity_name=username,
            description=f"Updated account: {username}"
        )

        # Emit real-time update
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                account_data = {
                    'id': account.id,
                    'username': data.get('username', getattr(account, 'username', account.instructor.email if hasattr(account, 'instructor') else '')),
                    'school_id': school_id,
                    'role': data.get('role', getattr(account, 'role', 'school_instructor')),
                    'type': data.get('role', getattr(account, 'role', 'school_instructor'))
                }
                
                # Add instructor name if it's an instructor account
                if hasattr(account, 'instructor') and account.instructor:
                    account_data['instructor_name'] = account.instructor.name
                
                current_app.socketio.emit('account_updated', {
                    'school_id': school_id,
                    'account': account_data
                }, room=f'school_{school_id}')
                print(f"📢 Emitting account_updated event: {{'school_id': {school_id}, 'account': {{'id': {account.id}, 'username': '{account_data['username']}'}}}}")
                print(f"✅ Successfully emitted to room: school_{school_id}")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")

        return jsonify({"success": True, "message": "Account updated successfully!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------
# Delete Account
# -------------------------------
@school_admin_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_account(id):
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

    try:
        # Check both possible tables
        account = SchoolAdmin.query.filter_by(id=id, school_id=school_id).first()
        if not account:
            account = SchoolInstructorAccount.query.filter_by(id=id, school_id=school_id).first()

        if not account:
            return jsonify({"success": False, "message": "Account not found."}), 404

        # Store account data for Socket.IO event before deletion
        account_data = {
            'id': account.id,
            'username': getattr(account, 'username', account.instructor.email if hasattr(account, 'instructor') else ''),
            'school_id': school_id,
            'role': getattr(account, 'role', 'school_instructor'),
            'type': getattr(account, 'role', 'school_instructor')
        }
        
        # Add instructor name if it's an instructor account
        if hasattr(account, 'instructor') and account.instructor:
            account_data['instructor_name'] = account.instructor.name

        # Log the activity before deletion
        log_activity(
            action='DELETE',
            entity_type='account',
            entity_id=id,
            entity_name=account_data['username'],
            description=f"Deleted account: {account_data['username']} ({account_data['role']})"
        )
        
        db.session.delete(account)
        db.session.commit()

        # Emit real-time update
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('account_deleted', {
                    'school_id': school_id,
                    'account': account_data
                }, room=f'school_{school_id}')
                print(f"📢 Emitting account_deleted event: {{'school_id': {school_id}, 'account': {{'id': {account_data['id']}, 'username': '{account_data['username']}'}}}}")
                print(f"✅ Successfully emitted to room: school_{school_id}")
        except Exception as e:
            print(f"❌ Socket.IO emit error: {e}")

        return jsonify({"success": True, "message": "Account deleted successfully!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

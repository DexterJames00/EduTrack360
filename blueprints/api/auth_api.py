from flask import Blueprint, request, jsonify, session
from models import SchoolInstructorAccount, Student, SchoolAdmin, Instructor, ParentAccount, db
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from functools import wraps

auth_api = Blueprint('auth_api', __name__, url_prefix='/api/auth')

# Secret key for JWT (should be in environment variable in production)
SECRET_KEY = 'your-secret-key-change-this-in-production'

def generate_token(user_id, username, role, school_id, user_type):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'school_id': school_id,
        'user_type': user_type,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Token is invalid or expired'}), 401
        
        request.user_id = payload['user_id']
        request.school_id = payload['school_id']
        request.role = payload['role']
        request.user_type = payload['user_type']
        
        return f(*args, **kwargs)
    
    return decorated

@auth_api.route('/login', methods=['POST'])
def login():
    """Login endpoint for mobile app"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Username and password are required'
        }), 400
    
    # Try to find user in different tables (parent -> instructor -> admin)
    user = None
    user_type = None
    school_id = None
    
    # Parent login: username is student_id, password is student's code
    try:
        student_id_int = int(username)
    except (TypeError, ValueError):
        student_id_int = None
    if student_id_int:
        student = Student.query.get(student_id_int)
        if student and student.code and password and password.strip() == (student.code or '').strip():
            # Find or create parent account for this student
            parent = ParentAccount.query.filter_by(student_id=student.id).first()
            if not parent:
                parent = ParentAccount(student_id=student.id, school_id=student.school_id)
                db.session.add(parent)
                db.session.commit()
            user = parent
            user_type = 'parent'
            school_id = student.school_id
    
    # Instructor accounts (login via instructor email)
    if not user:
        instructor = Instructor.query.filter_by(email=username).first()
        if instructor:
            instructor_account = SchoolInstructorAccount.query.filter_by(instructor_id=instructor.id).first()
            if instructor_account and instructor_account.password:
                stored = instructor_account.password
                is_hashed = stored.startswith(('scrypt:', 'pbkdf2:')) if stored else False
                password_ok = check_password_hash(stored, password) if is_hashed else (stored == password)
                if password_ok:
                    user = instructor_account
                    user_type = 'instructor'
                    school_id = instructor_account.school_id
    
    # Check school admin
    if not user:
        admin = SchoolAdmin.query.filter_by(username=username).first()
        if admin:
            stored = admin.password
            is_hashed = stored.startswith(('scrypt:', 'pbkdf2:')) if stored else False
            password_ok = check_password_hash(stored, password) if is_hashed else (stored == password)
            if password_ok:
                user = admin
                user_type = 'admin'
                school_id = admin.school_id
    
    # Check students (if they have accounts)
    # if not user:
    #     student = Student.query.filter_by(username=username).first()
    #     if student and check_password_hash(student.password, password):
    #         user = student
    #         user_type = 'student'
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
    
    # Get school_id if missing
    if school_id is None:
        school_id = getattr(user, 'school_id', None)
    
    # Get user details based on type
    if user_type == 'parent':
        # Parent info based on student
        st = Student.query.get(user.student_id)
        first_name = f"Parent of {st.first_name}" if st else 'Parent'
        last_name = f"{st.last_name}" if st else ''
        email = None
    elif user_type == 'instructor' and hasattr(user, 'instructor') and user.instructor:
        first_name = user.instructor.name.split()[0] if user.instructor.name else username
        last_name = ' '.join(user.instructor.name.split()[1:]) if len(user.instructor.name.split()) > 1 else ''
        email = user.instructor.email
    elif user_type == 'admin':
        first_name = username
        last_name = ''
        email = None
    else:
        first_name = username
        last_name = ''
        email = None
    
    # Generate token
    # Username to embed/display
    display_username = username if user_type != 'parent' else str(user.student_id)
    token = generate_token(user.id, display_username, user_type, school_id, user_type)
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': display_username,
            'email': email,
            'role': user_type,
            'schoolId': school_id,
            'firstName': first_name,
            'lastName': last_name
        },
        'message': 'Login successful'
    }), 200

@auth_api.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout endpoint"""
    return jsonify({'success': True}), 200

@auth_api.route('/verify', methods=['GET'])
@token_required
def verify():
    """Verify token validity"""
    return jsonify({'valid': True}), 200

@auth_api.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change password for instructor/admin accounts.
    Parents use student codes and cannot change passwords here.
    """
    data = request.get_json() or {}
    current_password = (data.get('current_password') or '').strip()
    new_password = (data.get('new_password') or '').strip()
    confirm_password = (data.get('confirm_password') or '').strip()

    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Password confirmation does not match'}), 400

    # Parents do not have changeable passwords in this model
    if request.user_type == 'parent':
        return jsonify({'success': False, 'message': 'Parents use student codes; password change is not available.'}), 400

    try:
        if request.user_type == 'instructor':
            acct = SchoolInstructorAccount.query.filter_by(id=request.user_id, school_id=request.school_id).first()
            if not acct:
                return jsonify({'success': False, 'message': 'Account not found'}), 404
            stored = acct.password
            if stored:
                is_hashed = stored.startswith(('scrypt:', 'pbkdf2:'))
                ok = check_password_hash(stored, current_password) if is_hashed else (stored == current_password)
                if not ok:
                    return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            else:
                # If no password set previously, require current_password to be empty
                if current_password:
                    return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            acct.password = generate_password_hash(new_password)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Password updated successfully'}), 200

        if request.user_type == 'admin':
            admin = SchoolAdmin.query.filter_by(id=request.user_id).first()
            if not admin:
                return jsonify({'success': False, 'message': 'Account not found'}), 404
            stored = admin.password
            if stored:
                is_hashed = stored.startswith(('scrypt:', 'pbkdf2:'))
                ok = check_password_hash(stored, current_password) if is_hashed else (stored == current_password)
                if not ok:
                    return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            else:
                if current_password:
                    return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
            admin.password = generate_password_hash(new_password)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Password updated successfully'}), 200

        return jsonify({'success': False, 'message': 'This account type cannot change password here'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to change password: {e}'}), 500

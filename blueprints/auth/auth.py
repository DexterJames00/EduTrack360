from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import MainAdmin, SchoolAdmin, SchoolInstructorAccount, Instructor
from activity_logger import log_login, log_logout
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Try to authenticate as MainAdmin first
        main_admin_user = MainAdmin.query.filter_by(username=username).first()
        
        if main_admin_user:
            # Check if password is hashed or plain text (for backward compatibility)
            password_valid = False
            if main_admin_user.password.startswith('scrypt:') or main_admin_user.password.startswith('pbkdf2:'):
                # Hashed password
                password_valid = check_password_hash(main_admin_user.password, password)
            else:
                # Plain text password (legacy)
                password_valid = (main_admin_user.password == password)
            
            if password_valid:
                # Main Admin login
                session['user_id'] = main_admin_user.id
                session['username'] = main_admin_user.username
                session['user_type'] = 'main_admin'
                
                # Log the login
                log_login(main_admin_user.username, 'main_admin')
                
                flash(f'Welcome back, Main Admin {main_admin_user.username}!', 'success')
                return redirect(url_for('main_admin.dashboard'))

        # Try to authenticate as SchoolAdmin
        school_admin_user = SchoolAdmin.query.filter_by(username=username).first()
        
        if school_admin_user:
            # Check if password is hashed or plain text (for backward compatibility)
            password_valid = False
            if school_admin_user.password.startswith('scrypt:') or school_admin_user.password.startswith('pbkdf2:'):
                # Hashed password
                password_valid = check_password_hash(school_admin_user.password, password)
            else:
                # Plain text password (legacy)
                password_valid = (school_admin_user.password == password)
            
            if password_valid:
                # School Admin login - get school code
                from models import School
                school = School.query.get(school_admin_user.school_id)
                school_code = school.school_code if school else None
                
                session['user_id'] = school_admin_user.id
                session['username'] = school_admin_user.username
                session['role'] = school_admin_user.role
                session['school_id'] = school_admin_user.school_id
                session['school_code'] = school_code
                session['user_type'] = 'school_admin'
                
                # Log the login
                log_login(school_admin_user.username, 'school_admin', school_admin_user.school_id)
                
                flash(f'Welcome back, {school_admin_user.username}!', 'success')
                return redirect(url_for('school_admin.dashboard'))
        
        # Try to authenticate as Instructor (via email)
        instructor = Instructor.query.filter_by(email=username).first()
        if instructor:
            # Check if this instructor has an account
            instructor_account = SchoolInstructorAccount.query.filter_by(instructor_id=instructor.id).first()
            
            if instructor_account and instructor_account.password:
                # Check password against stored hash
                if check_password_hash(instructor_account.password, password):
                    session['user_id'] = instructor_account.id
                    session['username'] = instructor.email
                    session['role'] = 'school_instructor'
                    session['school_id'] = instructor_account.school_id
                    session['instructor_id'] = instructor.id
                    session['instructor_name'] = instructor.name
                    session['user_type'] = 'school_instructor'
                    flash(f'Welcome back, {instructor.name}!', 'success')
                    return redirect(url_for('instructor.instructor_dashboard.dashboard'))
        
        # If no valid authentication found
        flash('Invalid username or password', 'danger')

    return render_template('landing.html')


@auth_bp.route('/logout')
def logout():
    # Log the logout before clearing session
    username = session.get('username', 'Unknown User')
    user_type = session.get('user_type', 'unknown')
    school_id = session.get('school_id')
    
    log_logout(username, user_type, school_id)
    
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

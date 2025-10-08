from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import SchoolAdmin as school_admin

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = school_admin.query.filter_by(username=username).first() 

        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['school_id'] = user.school_id
            return redirect(url_for('school_admin.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('landing.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

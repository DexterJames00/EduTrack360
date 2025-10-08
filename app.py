from flask import Flask, render_template
from database import db
from instance.config import Config

# Initialize app and config
app = Flask(__name__)
app.config.from_object(Config)

# SQLAlchemy setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/attendance_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Import blueprints
from blueprints.auth.auth import auth_bp
from blueprints.main_admin.main_admin_dashboard import main_admin_bp
from blueprints.school_admin.school_admin_dashboard import school_admin_bp
from blueprints.instructor.instructor_dashboard import instructor_bp    
from blueprints.school_admin.crud_intructor import school_admin_bp as crud_instructor_bp
from blueprints.school_admin.crud_accounts import school_admin_bp as crud_accounts_bp
from blueprints.school_admin.crud_section import school_admin_bp as crud_section_bp
from blueprints.school_admin.crud_student import school_admin_bp as crud_student_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_admin_bp)
app.register_blueprint(school_admin_bp)
app.register_blueprint(instructor_bp)
app.register_blueprint(crud_instructor_bp)  
app.register_blueprint(crud_accounts_bp)
app.register_blueprint(crud_section_bp) 
app.register_blueprint(crud_student_bp)

@app.route('/')
def home():
    return render_template('landing.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

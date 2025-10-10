from flask import Flask, render_template
from database import db
from instance.config import Config
import atexit
import signal
import sys

# Initialize app and config
app = Flask(__name__)
app.config.from_object(Config)

# SQLAlchemy setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin123@localhost/attendance_db'
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
from blueprints.school_admin.crud_subject import school_admin_bp as crud_subject_bp
from blueprints.school_admin.crud_assignment import assignment_bp as crud_assignment_bp
from blueprints.school_admin.crud_telegram import telegram_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_admin_bp)
app.register_blueprint(school_admin_bp)
app.register_blueprint(instructor_bp)
app.register_blueprint(crud_instructor_bp)  
app.register_blueprint(crud_accounts_bp)
app.register_blueprint(crud_section_bp) 
app.register_blueprint(crud_student_bp)
app.register_blueprint(crud_subject_bp)
app.register_blueprint(crud_assignment_bp)
app.register_blueprint(telegram_bp, url_prefix='/school_admin')

@app.route('/')
def home():
    return render_template('landing.html')

# Cleanup function for when app shuts down
def cleanup_on_exit():
    """Clean up resources when app shuts down"""
    try:
        from auto_telegram_setup import cleanup_auto_setup
        cleanup_auto_setup()
    except:
        pass

# Register cleanup functions
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, lambda s, f: (cleanup_on_exit(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s, f: (cleanup_on_exit(), sys.exit(0)))

if __name__ == '__main__':
    # Initialize auto-setup system
    try:
        from auto_telegram_setup import initialize_auto_setup, start_auto_setup
        
        print("🚀 Starting Flask app with auto Telegram bot setup...")
        
        # Initialize the auto-setup system
        auto_setup_instance = initialize_auto_setup(app, flask_port=5000)
        
        # Start auto-setup in background (starts after Flask is running)
        start_auto_setup(delay=3)
        
        print("✅ Auto-setup initialized! Starting Flask server...")
        
    except ImportError as e:
        print("⚠️  Auto-setup not available. Install missing packages:")
        print("   pip install pyngrok requests")
        print("🚀 Starting Flask app without auto-setup...")
    except Exception as e:
        print(f"⚠️  Auto-setup initialization failed: {e}")
        
        # Fallback to simple webhook setup
        try:
            print("� Trying simple webhook setup...")
            from simple_webhook_setup import quick_setup
            import threading
            import time
            
            def fallback_setup():
                time.sleep(3)  # Wait for Flask to start
                quick_setup(app, "https://adc380f07bf3.ngrok-free.app")
            
            setup_thread = threading.Thread(target=fallback_setup, daemon=True)
            setup_thread.start()
            
        except Exception as fallback_error:
            print(f"⚠️  Fallback setup also failed: {fallback_error}")
            print("�🚀 Starting Flask app without webhook setup...")
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)

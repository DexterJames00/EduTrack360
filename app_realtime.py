from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import db
from instance.config import Config
from datetime import datetime
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

# Initialize Socket.IO with threading async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Attach socketio to app for activity_logger access
app.socketio = socketio

# Import blueprints
from blueprints.auth.auth import auth_bp
from blueprints.main_admin.main_admin_dashboard import main_admin_bp
from blueprints.school_admin.school_admin_dashboard import school_admin_bp
from blueprints.instructor.instructor_dashboard import instructor_bp    
from blueprints.school_admin.crud_intructor import school_admin_bp as crud_instructor_bp
from blueprints.school_admin.crud_accounts import school_admin_bp as crud_accounts_bp
from blueprints.school_admin.crud_section import sections_bp as crud_section_bp
from blueprints.school_admin.crud_student import school_admin_bp as crud_student_bp
from blueprints.school_admin.crud_subject import subjects_bp as crud_subject_bp
from blueprints.school_admin.crud_assignment import assignment_bp as crud_assignment_bp
from blueprints.school_admin.crud_telegram import telegram_bp
from blueprints.school_admin.logs import logs_bp

# Import mobile app API blueprints
from blueprints.api.auth_api import auth_api
from blueprints.api.messaging_api import messaging_api
from blueprints.api.school_api import school_api
try:
    from blueprints.api.attendance_api import attendance_api
except Exception as e:
    attendance_api = None

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
app.register_blueprint(logs_bp)

# Register mobile app API blueprints
app.register_blueprint(auth_api)
app.register_blueprint(messaging_api)
app.register_blueprint(school_api)
if attendance_api is not None:
    app.register_blueprint(attendance_api)

# Make socketio available to blueprints
app.socketio = socketio

@app.route('/')
def home():
    return render_template('landing.html')

# Socket.IO Event Handlers
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    print(f"📍 Connection from: {request.environ.get('REMOTE_ADDR', 'unknown')}")
    print(f"🌐 Referer: {request.environ.get('HTTP_REFERER', 'unknown')}")
    emit('status', {'msg': 'Connected to real-time server'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_school_room')
def handle_join_school_room(data):
    """Handle user joining their school's log room"""
    school_id = data.get('school_id')
    if school_id:
        join_room(f'school_{school_id}')
        print(f"🏠 User joined school_{school_id} room")
        # Send confirmation to the client
        emit('status', {'message': f'Joined school_{school_id} room', 'type': 'success'})

@socketio.on('join_school')
def handle_join_school(data):
    """Handle mobile app user joining their school room"""
    school_id = data.get('schoolId')
    if school_id:
        room = f'school_{school_id}'
        join_room(room)
        print(f"📱 Mobile user joined {room}")
        emit('joined', {'room': room})

@socketio.on('send_message')
def handle_send_message(data):
    """Handle real-time message sending from mobile app"""
    # This is optional - messages are primarily sent via REST API
    # Can be used for typing indicators or other real-time features
    pass

@socketio.on('typing')
def handle_typing(data):
    """Relay typing indicator events to school room.
    Expected payload: { schoolId, conversationId, userId, isTyping }
    """
    school_id = (data or {}).get('schoolId')
    if not school_id:
        return
    try:
        emit_payload = {
            'conversationId': data.get('conversationId'),
            'userId': data.get('userId'),
            'isTyping': bool(data.get('isTyping')),
        }
        socketio.emit('typing', emit_payload, room=f'school_{school_id}')
    except Exception as e:
        print(f"typing relay error: {e}")

@socketio.on('join')
def handle_join():
    """Generic join handler for backward compatibility"""
    if 'school_id' in session:
        school_id = session['school_id']
        join_room(f'school_{school_id}')
        print(f"🏠 User joined school_{school_id} room (generic handler)")
        # Send confirmation to the client
        emit('status', {'message': f'Joined school_{school_id} room (generic)', 'type': 'success'})
    else:
        print("❌ Unauthenticated user tried to join room")
        emit('status', {'message': 'Authentication required', 'type': 'error'})

@socketio.on('test_logs_dashboard')
def handle_test_logs_dashboard(data):
    """Test handler for logs dashboard Socket.IO functionality"""
    school_id = data.get('school_id')
    print(f"🧪 Test event received from logs dashboard for school_{school_id}")
    
    # Send test response back
    emit('test_response', {
        'message': 'Test successful!',
        'school_id': school_id,
        'timestamp': str(datetime.now())
    })
    
    # Also test emitting to the room
    if school_id:
        socketio.emit('test_response', {
            'message': 'Room broadcast test successful!',
            'school_id': school_id,
            'timestamp': str(datetime.now())
        }, room=f'school_{school_id}')

@socketio.on('logs_dashboard_ready')
def handle_logs_dashboard_ready(data):
    """Special handler when logs dashboard is ready"""
    school_id = data.get('school_id')
    print(f"📊 Logs dashboard ready for school_{school_id}")
    print(f"📍 Dashboard connection from: {request.environ.get('REMOTE_ADDR', 'unknown')}")
    
    # Immediately join the room
    if school_id:
        join_room(f'school_{school_id}')
        print(f"🏠 Logs dashboard joined school_{school_id} room")
        
        # Send confirmation
        emit('logs_dashboard_confirmed', {
            'message': f'Dashboard connected to school_{school_id}',
            'school_id': school_id
        })

@socketio.on('leave_school_room')
def handle_leave_school_room(data):
    """Leave a school-specific room"""
    school_id = data.get('school_id')
    if school_id:
        room_name = f'school_{school_id}'
        leave_room(room_name)
        emit('status', {'msg': f'Left school room {school_id}'})
        print(f'Client {request.sid} left school room {school_id}')

@socketio.on('join_instructor_room')
def handle_join_instructor_room(data):
    """Join an instructor-specific room for real-time updates"""
    instructor_id = data.get('instructor_id')
    if instructor_id:
        room_name = f'instructor_{instructor_id}'
        join_room(room_name)
        emit('status', {'msg': f'Joined instructor room {instructor_id}'})
        print(f'Client {request.sid} joined instructor room {instructor_id}')

@socketio.on('request_dashboard_update')
def handle_dashboard_update_request(data):
    """Handle real-time dashboard update requests"""
    from models import Student, Instructor, Subject, Section, Attendance
    from sqlalchemy import func
    from datetime import datetime
    
    school_id = data.get('school_id')
    if not school_id:
        return
    
    try:
        # Get real-time statistics
        total_students = Student.query.filter_by(school_id=school_id).count()
        total_instructors = Instructor.query.filter_by(school_id=school_id).count() 
        total_subjects = Subject.query.filter_by(school_id=school_id).count()
        total_sections = Section.query.filter_by(school_id=school_id).count()
        
        # Today's attendance
        today = datetime.now().date()
        today_attendance = Attendance.query.join(Student).filter(
            Student.school_id == school_id,
            func.date(Attendance.created_at) == today
        ).count()
        
        # Connected students (with Telegram)
        connected_students = Student.query.filter_by(school_id=school_id).filter(
            Student.telegram_chat_id.isnot(None)
        ).count()
        
        stats = {
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_subjects': total_subjects,
            'total_sections': total_sections,
            'today_attendance': today_attendance,
            'connected_students': connected_students,
            'timestamp': datetime.now().isoformat()
        }
        
        # Emit to specific school room
        room_name = f'school_{school_id}'
        socketio.emit('dashboard_stats_update', stats, room=room_name)
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        emit('error', {'msg': 'Failed to get dashboard statistics'})

if __name__ == '__main__':
    # Start Flask-SocketIO app
    print("🚀 Starting Real-time Flask app with Socket.IO...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
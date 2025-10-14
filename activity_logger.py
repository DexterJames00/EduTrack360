from flask import session, request
from models import ActivityLog, db
import datetime


def log_activity(action, entity_type, entity_id=None, entity_name=None, description=None):
    """
    Log user activity to the database
    
    Args:
        action (str): The action performed (CREATE, UPDATE, DELETE, LOGIN, LOGOUT)
        entity_type (str): Type of entity (student, instructor, subject, section, account, etc.)
        entity_id (int, optional): ID of the affected entity
        entity_name (str, optional): Name/description of the affected entity
        description (str, optional): Detailed description of the action
    """
    try:
        # Get user info from session
        user_id = session.get('user_id')
        username = session.get('username', 'Unknown User')
        user_role = session.get('user_type', 'unknown')
        school_id = session.get('school_id')
        
        # Get request info
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Create activity log entry
        activity_log = ActivityLog(
            school_id=school_id,
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action.upper(),
            entity_type=entity_type.lower(),
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.datetime.utcnow()
        )
        
        db.session.add(activity_log)
        db.session.commit()
        
        # Emit real-time log update to logs dashboard
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio') and school_id:
                print(f"📡 Emitting new_activity_log to room school_{school_id}")
                current_app.socketio.emit('new_activity_log', {
                    'school_id': school_id,
                    'log': activity_log.to_dict()
                }, room=f'school_{school_id}')
                print(f"✅ new_activity_log event emitted successfully")
            else:
                print(f"⚠️ No socketio instance found or no school_id")
        except Exception as e:
            print(f"❌ Failed to emit activity log: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"📝 Activity logged: {username} ({user_role}) {action} {entity_type} - {entity_name}")
        
    except Exception as e:
        print(f"❌ Failed to log activity: {e}")
        # Don't let logging errors break the main functionality
        db.session.rollback()


def log_login(username, user_role, school_id=None):
    """Log user login activity"""
    try:
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        activity_log = ActivityLog(
            school_id=school_id,
            user_id=session.get('user_id'),
            username=username,
            user_role=user_role,
            action='LOGIN',
            entity_type='auth',
            entity_name=f"{username} logged in",
            description=f"User {username} ({user_role}) logged into the system",
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.datetime.utcnow()
        )
        
        db.session.add(activity_log)
        db.session.commit()
        
        print(f"🔑 Login logged: {username} ({user_role})")
        
    except Exception as e:
        print(f"❌ Failed to log login: {e}")
        db.session.rollback()


def log_logout(username, user_role, school_id=None):
    """Log user logout activity"""
    try:
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        activity_log = ActivityLog(
            school_id=school_id,
            user_id=session.get('user_id'),
            username=username,
            user_role=user_role,
            action='LOGOUT',
            entity_type='auth',
            entity_name=f"{username} logged out",
            description=f"User {username} ({user_role}) logged out of the system",
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.datetime.utcnow()
        )
        
        db.session.add(activity_log)
        db.session.commit()
        
        print(f"🚪 Logout logged: {username} ({user_role})")
        
    except Exception as e:
        print(f"❌ Failed to log logout: {e}")
        db.session.rollback()
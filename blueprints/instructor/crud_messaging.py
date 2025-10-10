from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database import db
from models import Student, Notification, TelegramConfig
import requests
from datetime import datetime
from sqlalchemy import func

messaging_bp = Blueprint('instructor_messaging', __name__)

@messaging_bp.route('/message/send', methods=['POST'])
def send_message():
    """Send message to student's parent via Telegram"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        message = data.get('message')
        
        if not student_id or not message:
            return jsonify({'error': 'Student ID and message are required'}), 400
        
        instructor_id = session['instructor_id']
        school_id = session['school_id']
        
        # Get student details
        student = Student.query.filter_by(id=student_id, school_id=school_id).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Check if student has Telegram connected
        if not student.telegram_chat_id:
            return jsonify({'error': 'Student does not have Telegram connected'}), 400
        
        # Get bot configuration for the school
        telegram_config = TelegramConfig.query.filter_by(school_id=school_id).first()
        if not telegram_config:
            return jsonify({'error': 'Telegram bot not configured for this school'}), 400
        
        # Format message with student and instructor details
        instructor_name = session.get('instructor_name', 'Instructor')
        formatted_message = f"""
📚 *ATTENDANCE NOTIFICATION*

👤 **Student:** {student.first_name} {student.last_name}
👨‍🏫 **From:** {instructor_name}
📅 **Date:** {datetime.now().strftime('%B %d, %Y')}

💬 **Message:**
{message}

---
*Sent via EduTrack360 Attendance System*
        """.strip()
        
        # Send message via Telegram
        success = send_telegram_message(
            telegram_config.bot_token,
            student.telegram_chat_id,
            formatted_message
        )
        
        # Create notification record
        notification = Notification(
            student_id=student_id,
            type='SMS',  # Using SMS type for Telegram messages
            message=message,
            status='Sent' if success else 'Failed'
        )
        db.session.add(notification)
        db.session.commit()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Message sent successfully to {student.first_name} {student.last_name}'
            })
        else:
            return jsonify({'error': 'Failed to send message'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error sending message: {str(e)}'}), 500

def send_telegram_message(bot_token, chat_id, message):
    """Send message via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

@messaging_bp.route('/message/templates', methods=['GET'])
def get_message_templates():
    """Get pre-defined message templates"""
    templates = [
        {
            'id': 'attendance_warning',
            'name': 'Attendance Warning',
            'message': 'Dear Parent, your child has been absent from class multiple times. Please ensure regular attendance to avoid academic issues.'
        },
        {
            'id': 'late_warning',
            'name': 'Tardiness Notice',
            'message': 'Dear Parent, your child has been frequently late to class. Please help ensure they arrive on time.'
        },
        {
            'id': 'good_attendance',
            'name': 'Good Attendance',
            'message': 'Dear Parent, congratulations! Your child has maintained excellent attendance this month.'
        },
        {
            'id': 'behavior_concern',
            'name': 'Behavior Concern',
            'message': 'Dear Parent, we would like to discuss your child\'s behavior in class. Please contact the school at your earliest convenience.'
        },
        {
            'id': 'assignment_missing',
            'name': 'Missing Assignment',
            'message': 'Dear Parent, your child has missing assignments. Please remind them to complete and submit their homework on time.'
        },
        {
            'id': 'custom',
            'name': 'Custom Message',
            'message': 'Dear Parent, '
        }
    ]
    
    return jsonify({'templates': templates})

@messaging_bp.route('/message/history', methods=['GET'])
def message_history():
    """Get message history for instructor"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    instructor_id = session['instructor_id']
    school_id = session['school_id']
    
    # Get recent notifications
    history = db.session.query(
        Notification.id,
        Notification.message,
        Notification.status,
        Notification.timestamp,
        func.concat(Student.first_name, ' ', Student.last_name).label('student_name'),
        Student.grade_level,
        Student.parent_contact
    ).join(Student, Notification.student_id == Student.id)\
     .filter(Student.school_id == school_id)\
     .order_by(Notification.timestamp.desc())\
     .limit(50)\
     .all()
    
    history_list = []
    for record in history:
        history_list.append({
            'id': record.id,
            'student_name': record.student_name,
            'grade_level': record.grade_level,
            'message': record.message,
            'status': record.status,
            'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'parent_contact': record.parent_contact
        })
    
    return jsonify({'history': history_list})

@messaging_bp.route('/message/bulk', methods=['POST'])
def send_bulk_message():
    """Send message to multiple students"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        message = data.get('message')
        
        if not student_ids or not message:
            return jsonify({'error': 'Student IDs and message are required'}), 400
        
        instructor_id = session['instructor_id']
        school_id = session['school_id']
        instructor_name = session.get('instructor_name', 'Instructor')
        
        # Get bot configuration
        telegram_config = TelegramConfig.query.filter_by(school_id=school_id).first()
        if not telegram_config:
            return jsonify({'error': 'Telegram bot not configured'}), 400
        
        # Get students with Telegram connected
        students = Student.query.filter(
            Student.id.in_(student_ids),
            Student.school_id == school_id,
            Student.telegram_chat_id.isnot(None)
        ).all()
        
        success_count = 0
        failed_count = 0
        
        for student in students:
            # Format message
            formatted_message = f"""
📚 *BULK NOTIFICATION*

👤 **Student:** {student.first_name} {student.last_name}
👨‍🏫 **From:** {instructor_name}
📅 **Date:** {datetime.now().strftime('%B %d, %Y')}

💬 **Message:**
{message}

---
*Sent via EduTrack360 Attendance System*
            """.strip()
            
            # Send message
            success = send_telegram_message(
                telegram_config.bot_token,
                student.telegram_chat_id,
                formatted_message
            )
            
            # Create notification record
            notification = Notification(
                student_id=student.id,
                type='SMS',
                message=message,
                status='Sent' if success else 'Failed'
            )
            db.session.add(notification)
            
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Messages sent: {success_count} successful, {failed_count} failed',
            'success_count': success_count,
            'failed_count': failed_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error sending bulk messages: {str(e)}'}), 500

@messaging_bp.route('/message/stats', methods=['GET'])
def messaging_stats():
    """Get messaging statistics"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    school_id = session['school_id']
    
    # Get stats for the past 30 days
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Total messages sent
    total_messages = Notification.query.join(Student)\
        .filter(Student.school_id == school_id)\
        .filter(Notification.timestamp >= thirty_days_ago)\
        .count()
    
    # Successful messages
    successful_messages = Notification.query.join(Student)\
        .filter(Student.school_id == school_id)\
        .filter(Notification.timestamp >= thirty_days_ago)\
        .filter(Notification.status == 'Sent')\
        .count()
    
    # Students with Telegram connected
    telegram_connected = Student.query.filter_by(school_id=school_id)\
        .filter(Student.telegram_chat_id.isnot(None))\
        .count()
    
    # Total students
    total_students = Student.query.filter_by(school_id=school_id).count()
    
    return jsonify({
        'total_messages': total_messages,
        'successful_messages': successful_messages,
        'failed_messages': total_messages - successful_messages,
        'telegram_connected': telegram_connected,
        'total_students': total_students,
        'connection_rate': round((telegram_connected / total_students * 100) if total_students > 0 else 0, 1)
    })
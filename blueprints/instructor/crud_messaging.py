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
        subject_name = data.get('subject_name', 'Current Subject')  # Get subject from request
        
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
            return jsonify({
                'error': f'{student.first_name} {student.last_name} does not have Telegram connected',
                'student_name': f'{student.first_name} {student.last_name}',
                'no_telegram': True
            }), 400
        
        # Get global bot configuration (active bot)
        telegram_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not telegram_config:
            return jsonify({'error': 'No active telegram bot configuration found'}), 400
        
        # Format message with student, instructor, and subject details
        instructor_name = session.get('instructor_name', 'Instructor')
        formatted_message = f"""📚 *ACADEMIC NOTIFICATION*

👤 **Student:** {student.first_name} {student.last_name}
📖 **Subject:** {subject_name}
👨‍🏫 **From:** {instructor_name}
🏫 **School:** {student.school.name if student.school else 'School'}
📅 **Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

💬 **Message:**
{message}

---
*This is an automated message from your school's attendance system. Please contact your instructor if you have any questions.*"""
        
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
                'message': f'Message sent successfully to {student.first_name} {student.last_name}',
                'student_name': f'{student.first_name} {student.last_name}',
                'subject_name': subject_name,
                'sent_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
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
            'title': 'Attendance Warning',
            'message': 'Dear Parent, your child is showing concerning attendance patterns in {subject}. Please ensure regular attendance to avoid academic issues.'
        },
        {
            'id': 'dropping_candidate',
            'title': 'Dropping Candidate',
            'message': 'Dear Parent, your child is a candidate for dropping due to attendance issues in {subject}. Immediate action is required to improve attendance.'
        },
        {
            'id': 'improvement_needed',
            'title': 'Improvement Needed',
            'message': 'Dear Parent, your child needs to improve their attendance in {subject}. Please discuss the importance of regular class attendance with them.'
        },
        {
            'id': 'excellent_attendance',
            'title': 'Excellent Attendance',
            'message': 'Dear Parent, congratulations! Your child has maintained excellent attendance in {subject}. Keep up the good work!'
        }
    ]
    
    return jsonify({'templates': templates})

@messaging_bp.route('/notifications/history', methods=['GET'])
def get_notification_history():
    """Get notification history for instructor"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        school_id = session['school_id']
        
        # Get recent notifications
        notifications = db.session.query(
            Notification.id,
            Notification.message,
            Notification.status,
            Notification.created_at,
            Student.first_name,
            Student.last_name
        ).join(Student, Notification.student_id == Student.id)\
         .filter(Student.school_id == school_id)\
         .order_by(Notification.created_at.desc())\
         .limit(50)\
         .all()
        
        notification_list = []
        for notif in notifications:
            notification_list.append({
                'id': notif.id,
                'student_name': f"{notif.first_name} {notif.last_name}",
                'message': notif.message,
                'status': notif.status,
                'sent_at': notif.created_at.strftime('%B %d, %Y at %I:%M %p')
            })
        
        return jsonify({'notifications': notification_list})
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving notifications: {str(e)}'}), 500

@messaging_bp.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification statistics"""
    if 'instructor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    try:
        school_id = session['school_id']
        
        # Get notification statistics
        total_notifications = db.session.query(Notification)\
            .join(Student, Notification.student_id == Student.id)\
            .filter(Student.school_id == school_id)\
            .count()
        
        successful_notifications = db.session.query(Notification)\
            .join(Student, Notification.student_id == Student.id)\
            .filter(Student.school_id == school_id)\
            .filter(Notification.status == 'Sent')\
            .count()
        
        failed_notifications = db.session.query(Notification)\
            .join(Student, Notification.student_id == Student.id)\
            .filter(Student.school_id == school_id)\
            .filter(Notification.status == 'Failed')\
            .count()
        
        # Get students without Telegram
        students_without_telegram = db.session.query(Student)\
            .filter(Student.school_id == school_id)\
            .filter(Student.telegram_chat_id.is_(None))\
            .count()
        
        students_with_telegram = db.session.query(Student)\
            .filter(Student.school_id == school_id)\
            .filter(Student.telegram_chat_id.isnot(None))\
            .count()
        
        return jsonify({
            'total_notifications': total_notifications,
            'successful_notifications': successful_notifications,
            'failed_notifications': failed_notifications,
            'students_with_telegram': students_with_telegram,
            'students_without_telegram': students_without_telegram,
            'success_rate': round((successful_notifications / total_notifications * 100) if total_notifications > 0 else 0, 1)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving stats: {str(e)}'}), 500
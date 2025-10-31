from flask import Blueprint, request, jsonify, session
from database import db
from models import Student, Notification, Conversation, Message, SchoolInstructorAccount, ParentAccount, Subject
from datetime import datetime
from sqlalchemy import func, or_, and_

messaging_bp = Blueprint('instructor_messaging', __name__)

@messaging_bp.route('/message/send', methods=['POST'])
def send_message():
    """Send message to student's parent via in-app messaging"""
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
        
        # Ensure a ParentAccount exists for this student
        parent = ParentAccount.query.filter_by(student_id=student.id).first()
        if not parent:
            parent = ParentAccount(student_id=student.id, school_id=student.school_id)
            db.session.add(parent)
            db.session.commit()

        # Find instructor account
        instructor_id = session['instructor_id']
        school_id = session['school_id']
        instructor_account = SchoolInstructorAccount.query.filter_by(instructor_id=instructor_id, school_id=school_id).first()

        # Find or create a conversation between instructor and parent
        conversation = Conversation.query.filter(
            Conversation.school_id == school_id,
            or_(
                and_(
                    Conversation.participant1_id == (instructor_account.id if instructor_account else 0),
                    Conversation.participant1_type == 'instructor',
                    Conversation.participant2_id == parent.id,
                    Conversation.participant2_type == 'parent'
                ),
                and_(
                    Conversation.participant1_id == parent.id,
                    Conversation.participant1_type == 'parent',
                    Conversation.participant2_id == (instructor_account.id if instructor_account else 0),
                    Conversation.participant2_type == 'instructor'
                )
            )
        ).first()

        if not conversation:
            conversation = Conversation(
                school_id=school_id,
                participant1_id=(instructor_account.id if instructor_account else 0),
                participant1_type='instructor',
                participant2_id=parent.id,
                participant2_type='parent'
            )
            db.session.add(conversation)
            db.session.commit()

        # Build a nicely formatted message body
        instructor_name = session.get('instructor_name', 'Instructor')
        if not subject_name:
            # Try resolve subject name if possible
            subj = Subject.query.filter_by(school_id=school_id).first()
            subject_name = subj.name if subj else 'Subject'
        formatted_message = (
            f"📚 Academic Notification\n\n"
            f"👤 Student: {student.first_name} {student.last_name}\n"
            f"📖 Subject: {subject_name}\n"
            f"👨‍🏫 From: {instructor_name}\n"
            f"🏫 School: {student.school.name if student.school else 'School'}\n"
            f"📅 Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
            f"💬 Message:\n{message}"
        )

        # Create Message
        msg = Message(
            conversation_id=conversation.id,
            sender_id=(instructor_account.id if instructor_account else 0),
            sender_type='instructor',
            receiver_id=parent.id,
            receiver_type='parent',
            content=formatted_message,
            message_type='text'
        )
        db.session.add(msg)
        conversation.updated_at = datetime.now()
        db.session.commit()

        # Emit socket event to the school's room
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('new_message', {
                    'id': msg.id,
                    'conversationId': conversation.id,
                    'senderId': msg.sender_id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'type': msg.message_type
                }, room=f'school_{school_id}')
        except Exception as e:
            # Non-fatal
            print(f"Socket emit failed: {e}")

        # Record a notification log for history
        notification = Notification(
            student_id=student_id,
            type='SMS',
            message=message,
            status='Sent'
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Message sent successfully to {student.first_name} {student.last_name}',
            'student_name': f'{student.first_name} {student.last_name}',
            'subject_name': subject_name,
            'sent_at': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error sending message: {str(e)}'}), 500

## Telegram helper removed: messaging now delivered in-app via Socket.IO and Message model

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
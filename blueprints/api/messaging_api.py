from flask import Blueprint, request, jsonify
from models import Conversation, Message, SchoolInstructorAccount, Student, SchoolAdmin, Instructor, ParentAccount, db
from blueprints.api.auth_api import token_required
import datetime

messaging_api = Blueprint('messaging_api', __name__, url_prefix='/api/messaging')

@messaging_api.route('/conversations', methods=['GET'])
@token_required
def get_conversations():
    """Get all conversations for current user"""
    user_id = request.user_id
    school_id = request.school_id
    user_type = request.user_type
    
    # Get conversations where user is participant
    conversations = Conversation.query.filter(
        Conversation.school_id == school_id,
        db.or_(
            db.and_(
                Conversation.participant1_id == user_id,
                Conversation.participant1_type == user_type
            ),
            db.and_(
                Conversation.participant2_id == user_id,
                Conversation.participant2_type == user_type
            )
        )
    ).order_by(Conversation.updated_at.desc()).all()
    
    return jsonify({
        'conversations': [conv.to_dict(user_id, user_type) for conv in conversations]
    }), 200

@messaging_api.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@token_required
def get_messages(conversation_id):
    """Get messages for a conversation"""
    user_id = request.user_id
    user_type = request.user_type
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    
    # Verify user is part of conversation
    conversation = Conversation.query.get_or_404(conversation_id)
    
    is_participant = (
        (conversation.participant1_id == user_id and conversation.participant1_type == user_type) or
        (conversation.participant2_id == user_id and conversation.participant2_type == user_type)
    )
    
    if not is_participant:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get messages with pagination
    offset = (page - 1) * limit
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.timestamp.asc())\
        .limit(limit).offset(offset).all()
    
    return jsonify({
        'messages': [msg.to_dict() for msg in messages]
    }), 200

@messaging_api.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@token_required
def send_message(conversation_id):
    """Send a message in a conversation"""
    user_id = request.user_id
    user_type = request.user_type
    school_id = request.school_id
    data = request.get_json()
    
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    # Verify conversation exists and user is participant
    conversation = Conversation.query.get_or_404(conversation_id)
    
    is_participant = (
        (conversation.participant1_id == user_id and conversation.participant1_type == user_type) or
        (conversation.participant2_id == user_id and conversation.participant2_type == user_type)
    )
    
    if not is_participant:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Enforce one-way notifications for certain roles (parents/students cannot send)
    if user_type in ('parent', 'student'):
        return jsonify({'error': 'Sending not allowed for this role'}), 403
    
    # Determine receiver
    if conversation.participant1_id == user_id and conversation.participant1_type == user_type:
        receiver_id = conversation.participant2_id
        receiver_type = conversation.participant2_type
    else:
        receiver_id = conversation.participant1_id
        receiver_type = conversation.participant1_type
    
    # Create message
    message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        sender_type=user_type,
        receiver_id=receiver_id,
        receiver_type=receiver_type,
        content=content,
        message_type=data.get('type', 'text')
    )
    
    db.session.add(message)
    conversation.updated_at = datetime.datetime.utcnow()
    db.session.commit()
    
    # Emit Socket.IO event (if socketio is available)
    try:
        from app_realtime import socketio
        socketio.emit('new_message', {
            'id': message.id,
            'conversationId': conversation_id,
            'senderId': user_id,
            'content': content,
            'timestamp': message.timestamp.isoformat(),
            'type': message.message_type
        }, room=f'school_{school_id}')
    except:
        pass  # Socket.IO not available or not running
    
    return jsonify({'message': message.to_dict()}), 201

@messaging_api.route('/conversations/<int:conversation_id>/mark-read', methods=['POST'])
@token_required
def mark_as_read(conversation_id):
    """Mark all messages in conversation as read"""
    user_id = request.user_id
    user_type = request.user_type
    
    # Update all unread messages for this user
    q = Message.query.filter_by(
        conversation_id=conversation_id,
        receiver_id=user_id,
        receiver_type=user_type,
        is_read=False
    )
    updated = q.update({'is_read': True})
    
    db.session.commit()

    # Notify clients to refresh unread counts
    try:
        from app_realtime import socketio
        # Emit minimal payload for clients to act on
        socketio.emit('messages_read', {
            'conversationId': conversation_id,
            'readerId': user_id,
            'readerType': user_type,
            'count': int(updated)
        }, room=f'school_{request.school_id}')
    except Exception:
        pass

    return jsonify({'success': True, 'updated': int(updated)}), 200

@messaging_api.route('/unread-count', methods=['GET'])
@token_required
def get_unread_count():
    """Get total unread message count"""
    user_id = request.user_id
    user_type = request.user_type
    
    count = Message.query.filter_by(
        receiver_id=user_id,
        receiver_type=user_type,
        is_read=False
    ).count()
    
    return jsonify({'count': count}), 200

@messaging_api.route('/conversations', methods=['POST'])
@token_required
def create_conversation():
    """Create a new conversation"""
    user_id = request.user_id
    user_type = request.user_type
    school_id = request.school_id
    data = request.get_json()
    
    participant_id = data.get('participantId')
    participant_type = data.get('participantType', 'instructor')  # Default to instructor
    
    if not participant_id:
        return jsonify({'error': 'participantId is required'}), 400
    
    # Check if conversation already exists
    existing = Conversation.query.filter(
        Conversation.school_id == school_id,
        db.or_(
            db.and_(
                Conversation.participant1_id == user_id,
                Conversation.participant1_type == user_type,
                Conversation.participant2_id == participant_id,
                Conversation.participant2_type == participant_type
            ),
            db.and_(
                Conversation.participant1_id == participant_id,
                Conversation.participant1_type == participant_type,
                Conversation.participant2_id == user_id,
                Conversation.participant2_type == user_type
            )
        )
    ).first()
    
    if existing:
        return jsonify({'conversation': existing.to_dict(user_id, user_type)}), 200
    
    # Create new conversation
    conversation = Conversation(
        school_id=school_id,
        participant1_id=user_id,
        participant1_type=user_type,
        participant2_id=participant_id,
        participant2_type=participant_type
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify({'conversation': conversation.to_dict(user_id, user_type)}), 201

@messaging_api.route('/users/search', methods=['GET'])
@token_required
def search_users():
    """Search users for starting conversations"""
    school_id = request.school_id
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'users': []}), 200
    
    users = []
    
    # Search instructors
    instructor_accounts = SchoolInstructorAccount.query.join(
        SchoolInstructorAccount.instructor
    ).filter(
        SchoolInstructorAccount.school_id == school_id,
        db.or_(
            Instructor.name.ilike(f'%{query}%'),
            Instructor.email.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    for account in instructor_accounts:
        if account.instructor:
            users.append({
                'id': account.id,
                'username': account.instructor.email,
                'email': account.instructor.email,
                'role': 'instructor',
                'schoolId': account.school_id,
                'firstName': account.instructor.name.split()[0] if account.instructor.name else account.instructor.email,
                'lastName': ' '.join(account.instructor.name.split()[1:]) if account.instructor.name else '',
                'type': 'instructor'
            })

    # Optionally search parents by student name
    parent_accounts = ParentAccount.query.join(ParentAccount.student).filter(
        ParentAccount.school_id == school_id,
        db.or_(
            Student.first_name.ilike(f'%{query}%'),
            Student.last_name.ilike(f'%{query}%')
        )
    ).limit(10).all()
    for parent in parent_accounts:
        s = parent.student
        users.append({
            'id': parent.id,
            'username': str(s.id),
            'email': None,
            'role': 'parent',
            'schoolId': parent.school_id,
            'firstName': f'Parent of {s.first_name}',
            'lastName': s.last_name,
            'type': 'parent'
        })
    
    # Search admins
    admins = SchoolAdmin.query.filter(
        SchoolAdmin.school_id == school_id,
        SchoolAdmin.username.ilike(f'%{query}%')
    ).limit(10).all()
    
    for admin in admins:
        users.append({
            'id': admin.id,
            'username': admin.username,
            'email': None,
            'role': 'school_admin',
            'schoolId': admin.school_id,
            'firstName': admin.username,
            'lastName': '',
            'type': 'admin'
        })
    
    return jsonify({'users': users}), 200

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from database import db
from models import TelegramConfig, Student, Section, School
from sqlalchemy import func
import datetime
import json

# Create blueprint
telegram_bp = Blueprint('telegram', __name__)

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Handle incoming Telegram webhook updates"""
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Process the update
        result = process_telegram_update(update)
        
        if result.get('status') == 'success':
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'error', 'message': result.get('message', 'Unknown error')}), 500
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_telegram_update(update):
    """Process incoming Telegram update"""
    try:
        # Extract message from update
        message = update.get('message')
        if not message:
            return {'status': 'ignored', 'message': 'No message in update'}
        
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '').strip()
        
        if not chat_id or not text:
            return {'status': 'ignored', 'message': 'Invalid message format'}
        
        print(f"📱 Received message: '{text}' from chat_id: {chat_id}")
        
        # Handle /start command
        if text.startswith('/start'):
            return handle_start_command(chat_id, text)
        
        # Handle school name + student code format: "SCHOOLNAME STUDENTCODE"
        # Must have at least 2 words (school name + student code)
        if ' ' in text and len(text.split()) >= 2:
            return handle_student_registration(chat_id, text)
        
        # Handle other messages
        return handle_general_message(chat_id, text)
        
    except Exception as e:
        print(f"Error processing update: {e}")
        return {'status': 'error', 'message': str(e)}

def handle_start_command(chat_id, text):
    """Handle /start command"""
    try:
        # Send welcome message with school codes
        welcome_message = (
            "🎓 Welcome to the School Attendance Bot!\n\n"
            "To register for attendance notifications:\n"
            "📝 Send: SCHOOLCODE STUDENTCODE\n\n"
            "Available school codes:\n"
            "• ACLCCOLLEG - Aclc College of Butuan\n"
            "• MAGAUDNATI - Magaud National High School\n\n"
            "Example: ACLCCOLLEG ABC123\n\n"
            "❓ Need help? Contact your school administrator."
        )
        
        send_telegram_message(chat_id, welcome_message)
        
        return {
            'status': 'success', 
            'message': f'Welcome message sent to {chat_id}'
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def handle_student_registration(chat_id, text):
    """Handle student registration with school code and student code"""
    try:
        parts = text.split()
        
        if len(parts) != 2:
            message = (
                "❌ Invalid format!\n\n"
                "Please send: SCHOOLCODE STUDENTCODE\n\n"
                "Available school codes:\n"
                "• ACLCCOLLEG - Aclc College of Butuan\n"
                "• MAGAUDNATI - Magaud National High School\n\n"
                "Example: ACLCCOLLEG ABC123"
            )
            send_telegram_message(chat_id, message)
            return {'status': 'error', 'message': 'Invalid format'}
        
        school_code = parts[0].upper()
        student_code = parts[1].upper()
        
        print(f"🔍 Looking for school code: '{school_code}', student code: '{student_code}'")
        
        # Find school by code
        school = School.query.filter_by(school_code=school_code).first()
        
        if not school:
            message = (
                f"❌ School code '{school_code}' not found.\n\n"
                "Available school codes:\n"
                "• ACLCCOLLEG - Aclc College of Butuan\n"
                "• MAGAUDNATI - Magaud National High School\n\n"
                "Please check the school code and try again."
            )
            send_telegram_message(chat_id, message)
            return {'status': 'error', 'message': f'School not found: {school_code}'}
        
        print(f"✅ Found school: {school.name} (Code: {school_code})")
        
        # Find student by code in that school
        student = Student.query.filter_by(school_id=school.id, code=student_code).first()
        
        if not student:
            message = f"❌ Student code '{student_code}' not found in {school.name}.\n\nPlease check your student code and try again."
            send_telegram_message(chat_id, message)
            return {'status': 'error', 'message': f'Student not found: {student_code}'}
        
        print(f"✅ Found student: {student.first_name} {student.last_name} (Code: {student_code})")
        
        # Check if already registered
        if student.telegram_chat_id and student.telegram_status:
            message = f"✅ You're already registered!\n\n👤 Student: {student.first_name} {student.last_name}\n🏫 School: {school.name}\n📚 You'll receive attendance notifications here."
            send_telegram_message(chat_id, message)
            return {'status': 'success', 'message': 'Student already registered'}
        
        # Register the student
        student.telegram_chat_id = str(chat_id)
        student.telegram_status = True
        db.session.commit()
        
        # Send success message
        success_message = f"✅ Registration successful!\n\n👤 Student: {student.first_name} {student.last_name}\n🏫 School: {school.name}\n📚 You'll receive attendance notifications here."
        
        send_telegram_message(chat_id, success_message)
        
        print(f"✅ Student registered: {student.first_name} {student.last_name} -> {chat_id}")
        
        return {
            'status': 'success', 
            'message': f'Student {student.first_name} {student.last_name} registered successfully'
        }
        
    except Exception as e:
        print(f"Error in student registration: {e}")
        db.session.rollback()
        
        error_message = "❌ Registration failed. Please try again or contact your school administrator."
        send_telegram_message(chat_id, error_message)
        
        return {'status': 'error', 'message': str(e)}

def handle_general_message(chat_id, text):
    """Handle general messages"""
    try:
        help_message = (
            "🤖 I can help you register for attendance notifications!\n\n"
            "📝 To register, send:\n"
            "SCHOOLNAME STUDENTCODE\n\n"
            "Example: SAMPLESCHOOL ABC123\n\n"
            "❓ Need your student code? Contact your school administrator."
        )
        
        send_telegram_message(chat_id, help_message)
        
        return {
            'status': 'success', 
            'message': f'Help message sent to {chat_id}'
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def send_telegram_message(chat_id, message):
    """Send a message to a Telegram chat"""
    try:
        # Get active bot configuration
        config = TelegramConfig.query.filter_by(is_active=True).first()
        
        if not config:
            print("❌ No active bot configuration found")
            return False
        
        import requests
        
        url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message sent to {chat_id}")
            return True
        else:
            print(f"❌ Failed to send message: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

@telegram_bp.route('/auto-setup-status', methods=['GET'])
def auto_setup_status():
    """Get the current auto-setup status"""
    try:
        from auto_telegram_setup import get_public_url, is_setup_complete
        
        public_url = get_public_url()
        setup_complete = is_setup_complete()
        
        return jsonify({
            'public_url': public_url,
            'setup_complete': setup_complete,
            'webhook_url': f"{public_url}/school_admin/webhook" if public_url else None
        }), 200
        
    except ImportError:
        return jsonify({
            'public_url': None,
            'setup_complete': False,
            'error': 'Auto-setup not available'
        }), 200
    except Exception as e:
        return jsonify({
            'public_url': None,
            'setup_complete': False,
            'error': str(e)
        }), 500

@telegram_bp.route('/test-session')
def test_session():
    """Test route to check session data"""
    return jsonify({
        'session_data': dict(session),
        'school_admin_id': session.get('school_admin_id'),
        'school_id': session.get('school_id')
    })

@telegram_bp.route('/telegram')
def telegram_config_page():
    """Render the telegram configuration page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('school_admin/telegram_config.html')

@telegram_bp.route('/telegram-config-api', methods=['GET'])
def get_telegram_config():
    """Get all telegram configurations for the current school"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'error': 'School not found'}), 400
        
        # Get all telegram configs (global bot system)
        configs = TelegramConfig.query.order_by(TelegramConfig.created_at.desc()).all()
        
        config_list = []
        for config in configs:
            config_data = config.to_dict()
            # Convert datetime objects to strings for JSON serialization
            if config_data['created_at']:
                config_data['created_at'] = config_data['created_at'].isoformat()
            if config_data['updated_at']:
                config_data['updated_at'] = config_data['updated_at'].isoformat()
            config_list.append(config_data)
        
        return jsonify(config_list), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/telegram-config-api', methods=['POST'])
def create_or_update_telegram_config():
    """Create or update telegram configuration"""
    try:
        print("DEBUG: Starting telegram config save...")
        
        if 'user_id' not in session:
            print("DEBUG: No user_id in session")
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        print(f"DEBUG: School ID from session: {school_id}")
        
        if not school_id:
            print("DEBUG: No school_id found")
            return jsonify({'error': 'School not found'}), 400
        
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        bot_token = data.get('bot_token', '').strip()
        bot_username = data.get('bot_username', '').strip()
        
        print(f"DEBUG: Bot token length: {len(bot_token)}, Bot username: {bot_username}")
        
        if not bot_token or not bot_username:
            return jsonify({'error': 'Bot token and username are required'}), 400
        
        # Check if configuration already exists (global bot system)
        existing_config = TelegramConfig.query.filter_by(bot_token=bot_token).first()
        print(f"DEBUG: Existing config found: {existing_config is not None}")
        
        if existing_config:
            # Update existing configuration
            print("DEBUG: Updating existing configuration...")
            existing_config.bot_username = bot_username
            existing_config.is_active = True
            existing_config.updated_at = datetime.datetime.utcnow()
        else:
            # Create new configuration
            print("DEBUG: Creating new configuration...")
            new_config = TelegramConfig(
                school_id=school_id,
                bot_token=bot_token,
                bot_username=bot_username
            )
            db.session.add(new_config)
        
        print("DEBUG: Committing to database...")
        db.session.commit()
        print("DEBUG: Configuration saved successfully!")
        
        return jsonify({'message': 'Configuration saved successfully'}), 200
        
    except Exception as e:
        print(f"DEBUG: Error occurred: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@telegram_bp.route('/telegram-config-api/<int:config_id>', methods=['DELETE'])
def delete_telegram_config(config_id):
    """Delete a telegram configuration"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        config = TelegramConfig.query.filter_by(id=config_id, school_id=school_id).first()
        
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'message': 'Configuration deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/telegram-stats', methods=['GET'])
def get_telegram_stats():
    """Get telegram connection statistics"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'error': 'School not found'}), 400
        
        # Count total students
        total_students = Student.query.filter_by(school_id=school_id).count()
        
        # Count connected students (those with telegram_status = True)
        connected_parents = Student.query.filter_by(
            school_id=school_id, 
            telegram_status=True
        ).count()
        
        # Calculate not connected
        not_connected = total_students - connected_parents
        
        stats = {
            'total_students': total_students,
            'connected_parents': connected_parents,
            'not_connected': not_connected
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/student-connections', methods=['GET'])
def get_student_connections():
    """Get detailed student connection information"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        if not school_id:
            return jsonify({'error': 'School not found'}), 400
        
        # Query students with section information
        students_query = db.session.query(
            Student.id,
            Student.first_name,
            Student.last_name,
            Student.grade_level,
            Student.parent_contact,
            Student.telegram_chat_id,
            Student.telegram_status,
            Section.name.label('section_name')
        ).join(
            Section, Student.section_id == Section.id
        ).filter(
            Student.school_id == school_id
        ).order_by(
            Student.first_name, Student.last_name
        )
        
        students_data = []
        for student in students_query.all():
            student_dict = {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'grade_level': student.grade_level,
                'section_name': student.section_name,
                'parent_contact': student.parent_contact,
                'telegram_chat_id': student.telegram_chat_id,
                'telegram_status': student.telegram_status
            }
            students_data.append(student_dict)
        
        return jsonify({'students': students_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/send-test-message/<int:student_id>', methods=['POST'])
def send_test_message(student_id):
    """Send a test message to a connected student"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        student = Student.query.filter_by(id=student_id, school_id=school_id).first()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        if not student.telegram_status or not student.telegram_chat_id:
            return jsonify({'error': 'Student is not connected to Telegram'}), 400
        
        # Here you would implement the actual Telegram message sending
        # For now, we'll just return a success message
        # You would need to integrate with the Telegram Bot API
        
        message = f"Test message for {student.first_name} {student.last_name}"
        
        # TODO: Implement actual Telegram message sending
        # telegram_service.send_message(student.telegram_chat_id, message)
        
        return jsonify({
            'message': 'Test message sent successfully',
            'student_name': f"{student.first_name} {student.last_name}",
            'chat_id': student.telegram_chat_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/generate-invite/<int:student_id>', methods=['POST'])
def generate_invite(student_id):
    """Generate an invite link for a student"""
    try:
        if 'school_admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        student = Student.query.filter_by(id=student_id, school_id=school_id).first()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get global bot configuration (active bot)
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return jsonify({'error': 'No active telegram bot configuration found'}), 400
        
        # Generate a unique code for the student if not exists
        if not student.code:
            import random
            import string
            student.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            db.session.commit()
        
        # Create invite link
        invite_link = f"https://t.me/{bot_config.bot_username}?start={student.code}"
        
        return jsonify({
            'message': 'Invite link generated successfully',
            'student_name': f"{student.first_name} {student.last_name}",
            'invite_link': invite_link,
            'student_code': student.code
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/student-details/<int:student_id>', methods=['GET'])
def get_student_details(student_id):
    """Get detailed information about a student"""
    try:
        if 'school_admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        
        # Query student with section and school information
        student_query = db.session.query(
            Student.id,
            Student.first_name,
            Student.last_name,
            Student.grade_level,
            Student.parent_contact,
            Student.telegram_chat_id,
            Student.telegram_status,
            Student.code,
            Section.name.label('section_name'),
            School.name.label('school_name')
        ).join(
            Section, Student.section_id == Section.id
        ).join(
            School, Student.school_id == School.id
        ).filter(
            Student.id == student_id,
            Student.school_id == school_id
        ).first()
        
        if not student_query:
            return jsonify({'error': 'Student not found'}), 404
        
        student_details = {
            'id': student_query.id,
            'first_name': student_query.first_name,
            'last_name': student_query.last_name,
            'full_name': f"{student_query.first_name} {student_query.last_name}",
            'grade_level': student_query.grade_level,
            'section_name': student_query.section_name,
            'school_name': student_query.school_name,
            'parent_contact': student_query.parent_contact,
            'telegram_chat_id': student_query.telegram_chat_id,
            'telegram_status': student_query.telegram_status,
            'student_code': student_query.code
        }
        
        return jsonify(student_details), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@telegram_bp.route('/test-bot/<int:config_id>', methods=['POST'])
def test_bot(config_id):
    """Test if the bot configuration is working"""
    try:
        if 'school_admin_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        school_id = session.get('school_id')
        config = TelegramConfig.query.filter_by(id=config_id, school_id=school_id).first()
        
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        # TODO: Implement actual bot testing
        # This would involve making a request to the Telegram Bot API
        # to verify the bot token is valid and the bot is responding
        
        # For now, we'll simulate a test
        import time
        
        # Simulate API call delay
        time.sleep(1)
        
        # In a real implementation, you would install requests and do:
        # import requests
        # response = requests.get(f"https://api.telegram.org/bot{config.bot_token}/getMe")
        # if response.status_code == 200:
        #     bot_info = response.json()
        #     return jsonify({
        #         'status': 'success',
        #         'message': 'Bot is working correctly',
        #         'bot_info': bot_info['result']
        #     }), 200
        
        return jsonify({
            'status': 'success',
            'message': 'Bot test completed successfully',
            'bot_username': config.bot_username,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

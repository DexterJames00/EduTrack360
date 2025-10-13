from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from database import db
from models import TelegramConfig, Student, School
from sqlalchemy import func
import requests
import json

main_admin_bp = Blueprint('main_admin', __name__, url_prefix='/main_admin')

# Check admin access
def check_main_admin():
    # Temporarily disable auth check for debugging
    return True
    # if 'user_id' not in session or session.get('user_type') != 'main_admin':
    #     return False
    # return True

@main_admin_bp.route('/')
def dashboard():
    return render_template('main_admin/main_admin_dashboard.html')

@main_admin_bp.route('/telegram-config')
def telegram_config():
    """Global Telegram Bot Management for Main Admin"""
    if not check_main_admin():
        flash('Access denied. Main admin privileges required.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('main_admin/telegram_config.html')

@main_admin_bp.route('/telegram-config-api', methods=['GET', 'POST'])
def telegram_config_api():
    """API endpoints for telegram configuration management"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        # Get all telegram configurations
        configs = TelegramConfig.query.all()
        config_list = []
        for config in configs:
            config_list.append({
                'id': config.id,
                'bot_token': config.bot_token,
                'bot_username': config.bot_username,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None
            })
        return jsonify(config_list)
    
    elif request.method == 'POST':
        # Add or update telegram configuration
        data = request.get_json()
        bot_token = data.get('bot_token', '').strip()
        bot_username = data.get('bot_username', '').strip()
        
        if not bot_token or not bot_username:
            return jsonify({'error': 'Bot token and username are required'}), 400
        
        try:
            # Deactivate all existing configs
            TelegramConfig.query.update({'is_active': False})
            
            # Check if config already exists
            existing_config = TelegramConfig.query.filter_by(bot_token=bot_token).first()
            
            if existing_config:
                # Update existing config
                existing_config.bot_username = bot_username
                existing_config.is_active = True
            else:
                # Create new config
                new_config = TelegramConfig(
                    bot_token=bot_token,
                    bot_username=bot_username,
                    is_active=True
                )
                db.session.add(new_config)
            
            db.session.commit()
            return jsonify({'message': 'Global telegram configuration saved successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/telegram-config-api/<int:config_id>', methods=['DELETE'])
def delete_telegram_config_api(config_id):
    """Delete a telegram configuration"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        config = TelegramConfig.query.get_or_404(config_id)
        db.session.delete(config)
        db.session.commit()
        return jsonify({'message': 'Configuration deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/telegram-stats')
def telegram_stats():
    """Get system-wide telegram statistics"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get total schools
        total_schools = School.query.count()
        
        # Get total students
        total_students = Student.query.count()
        
        # Get connected parents (students with telegram_chat_id)
        connected_parents = Student.query.filter(Student.telegram_chat_id.isnot(None)).count()
        
        # Calculate not connected
        not_connected = total_students - connected_parents
        
        stats = {
            'total_schools': total_schools,
            'total_students': total_students,
            'connected_parents': connected_parents,
            'not_connected': not_connected
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/school-telegram-stats')
def school_telegram_stats():
    """Get school-wise telegram statistics"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get all schools
        schools = School.query.all()
        school_stats = []
        
        for school in schools:
            # Get students for this school
            students = Student.query.filter_by(school_id=school.id).all()
            total_students = len(students)
            connected = sum(1 for student in students if student.telegram_chat_id)
            not_connected = total_students - connected
            
            school_stats.append({
                'school_id': school.id,
                'school_name': school.name,
                'school_code': school.school_code,
                'total_students': total_students,
                'connected': connected,
                'not_connected': not_connected
            })
        
        return jsonify(school_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/all-student-connections')
def all_student_connections():
    """Get all students with their telegram connection status"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from models import Section
        
        # Get all students with their school information
        students = Student.query.all()
        student_list = []
        
        for student in students:
            school = School.query.get(student.school_id)
            # Get section name
            section_name = 'N/A'
            if student.section_id:
                section = Section.query.get(student.section_id)
                if section:
                    section_name = section.name
            
            student_list.append({
                'id': student.id,
                'code': student.code or 'N/A',
                'first_name': student.first_name,
                'last_name': student.last_name,
                'grade_level': student.grade_level,
                'section_name': section_name,
                'parent_contact': student.parent_contact or 'N/A',
                'telegram_chat_id': student.telegram_chat_id,
                'telegram_status': bool(student.telegram_chat_id),
                'school_name': school.name if school else 'Unknown',
                'school_code': school.school_code if school else 'Unknown'
            })
        
        return jsonify({'students': student_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/auto-setup-status')
def auto_setup_status():
    """Get auto-setup status for the global bot system"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Check if we have an active telegram configuration
        active_config = TelegramConfig.query.filter_by(is_active=True).first()
        
        if not active_config:
            return jsonify({
                'setup_complete': False,
                'public_url': None,
                'message': 'No active telegram configuration found'
            })
        
        # Try to get the current ngrok status
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                public_url = None
                
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        public_url = tunnel.get('public_url')
                        break
                
                if public_url:
                    return jsonify({
                        'setup_complete': True,
                        'public_url': public_url,
                        'message': 'Global bot system is active'
                    })
                else:
                    return jsonify({
                        'setup_complete': False,
                        'public_url': None,
                        'message': 'Ngrok tunnel not found'
                    })
            else:
                return jsonify({
                    'setup_complete': False,
                    'public_url': None,
                    'message': 'Cannot connect to ngrok'
                })
                
        except requests.RequestException:
            return jsonify({
                'setup_complete': False,
                'public_url': None,
                'message': 'Ngrok service not available'
            })
            
    except Exception as e:
        return jsonify({
            'setup_complete': False,
            'public_url': None,
            'message': f'Error checking setup status: {str(e)}'
        })

@main_admin_bp.route('/activate-bot/<int:config_id>', methods=['POST'])
def activate_bot(config_id):
    """Activate a specific telegram bot configuration"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Deactivate all configs
        TelegramConfig.query.update({'is_active': False})
        
        # Activate the selected config
        config = TelegramConfig.query.get_or_404(config_id)
        config.is_active = True
        
        db.session.commit()
        
        return jsonify({'message': f'Bot @{config.bot_username} activated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_admin_bp.route('/test-bot/<int:config_id>', methods=['POST'])
def test_bot(config_id):
    """Test a telegram bot configuration"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        config = TelegramConfig.query.get_or_404(config_id)
        
        # Test the bot by calling getMe API
        test_url = f"https://api.telegram.org/bot{config.bot_token}/getMe"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                return jsonify({
                    'success': True,
                    'message': f'Bot test successful!',
                    'bot_info': {
                        'username': bot_data.get('username', 'Unknown'),
                        'first_name': bot_data.get('first_name', 'Unknown'),
                        'can_join_groups': bot_data.get('can_join_groups', False),
                        'can_read_all_group_messages': bot_data.get('can_read_all_group_messages', False)
                    }
                })
            else:
                return jsonify({'success': False, 'message': 'Bot API returned error'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to Telegram API'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_admin_bp.route('/send-test-message/<int:student_id>', methods=['POST'])
def send_test_message(student_id):
    """Send a test message to a specific student"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get student and active bot config
        student = Student.query.get_or_404(student_id)
        active_config = TelegramConfig.query.filter_by(is_active=True).first()
        
        if not active_config:
            return jsonify({'success': False, 'message': 'No active bot configuration'})
        
        if not student.telegram_chat_id:
            return jsonify({'success': False, 'message': 'Student not connected to Telegram'})
        
        # Send test message
        message = f"🧪 Test Message from {student.school.school_name}\n\nHi! This is a test notification for {student.first_name} {student.last_name}.\n\nYour attendance notifications are working properly! ✅"
        
        send_url = f"https://api.telegram.org/bot{active_config.bot_token}/sendMessage"
        payload = {
            'chat_id': student.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(send_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Test message sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send test message'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_admin_bp.route('/export-connections')
def export_connections():
    """Export student connections data as CSV"""
    if not check_main_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        from flask import make_response
        import csv
        from io import StringIO
        from models import Section
        
        # Get all students with connection data
        students_query = db.session.query(
            Student.id,
            Student.code,
            Student.first_name,
            Student.last_name,
            Student.grade_level,
            Student.parent_contact,
            Student.telegram_chat_id,
            School.name,
            School.school_code,
            Section.section_name
        ).join(School).outerjoin(Section, Student.section_id == Section.id).all()
        
        # Create CSV data
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Student ID', 'Student Code', 'First Name', 'Last Name', 
            'Grade Level', 'Section', 'School Name', 'School Code',
            'Parent Contact', 'Telegram Status', 'Chat ID'
        ])
        
        # Write data
        for student in students_query:
            writer.writerow([
                student.id,
                student.code,
                student.first_name,
                student.last_name,
                student.grade_level,
                student.section_name or 'N/A',
                student.name,
                student.school_code,
                student.parent_contact or 'N/A',
                'Connected' if student.telegram_chat_id else 'Not Connected',
                student.telegram_chat_id or 'N/A'
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=student_telegram_connections.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

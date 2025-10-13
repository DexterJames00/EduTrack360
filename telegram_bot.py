"""
Telegram Bot Handler for Student Registration
This module handles Telegram bot interactions for linking students to their chat IDs
"""

import requests
from database import db
from models import Student, School, TelegramConfig
from sqlalchemy import func
import os
import json

class TelegramBot:
    def __init__(self, bot_token, school_id):
        self.bot_token = bot_token
        self.school_id = school_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Send a message to a Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
    
    def set_webhook(self, webhook_url):
        """Set webhook URL for the bot"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {'url': webhook_url}
            response = requests.post(url, json=data)
            return response.json()
        except Exception as e:
            print(f"Error setting webhook: {str(e)}")
            return None
    
    def get_bot_info(self):
        """Get bot information"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting bot info: {str(e)}")
            return None

def process_telegram_update(update_data, school_id):
    """Process incoming Telegram update and handle student registration"""
    try:
        if 'message' not in update_data:
            return {'status': 'ok', 'message': 'No message in update'}
        
        message = update_data['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '').strip()
        first_name = message['from'].get('first_name', '')
        username = message['from'].get('username', '')
        
        # Get global bot configuration (active bot)
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return {'status': 'error', 'message': 'No active bot configuration found'}
        
        bot = TelegramBot(bot_config.bot_token, school_id)
        
        # Check if this is a /start command with parameters
        if text.startswith('/start '):
            return handle_start_command(text, chat_id, school_id, bot)
        
        # Handle regular messages with school name and code
        elif text and len(text.split()) >= 2:
            return handle_manual_registration(text, chat_id, school_id, bot)
        
        # Send help message
        else:
            return send_help_message(chat_id, school_id, bot)
            
    except Exception as e:
        print(f"Error processing update: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def handle_start_command(text, chat_id, school_id, bot):
    """Handle /start command with student code"""
    try:
        # Extract the student code from /start command
        parts = text.split(' ', 1)
        if len(parts) <= 1:
            bot.send_message(chat_id, 
                "❌ Invalid invitation link. Please use the complete link provided by your school.")
            return {'status': 'error', 'message': 'No code provided'}
        
        student_code = parts[1].strip().upper()
        
        # Find student with matching code and school
        student = Student.query.filter_by(
            code=student_code,
            school_id=school_id
        ).first()
        
        if not student:
            bot.send_message(chat_id,
                "❌ Invalid student code or school. Please check your invitation link and try again.\n\n"
                "If you continue to have issues, please contact your school administrator.")
            return {'status': 'error', 'message': 'Student not found'}
        
        # Check if student is already linked to another chat
        if student.telegram_chat_id and student.telegram_chat_id != chat_id:
            bot.send_message(chat_id,
                f"⚠️ This student code is already linked to another Telegram account.\n"
                f"Student: {student.first_name} {student.last_name}\n\n"
                f"If this is your account, please contact your school administrator.")
            return {'status': 'error', 'message': 'Student already linked to different chat'}
        
        # Update student's telegram info
        student.telegram_chat_id = chat_id
        student.telegram_status = True
        db.session.commit()
        
        # Send confirmation message
        school_name = student.school.name if student.school else "your school"
        bot.send_message(chat_id,
            f"✅ <b>Successfully linked!</b>\n\n"
            f"👤 <b>Student:</b> {student.first_name} {student.last_name}\n"
            f"🏫 <b>School:</b> {school_name}\n"
            f"📚 <b>Grade:</b> {student.grade_level}\n\n"
            f"You will now receive attendance notifications from {school_name}.\n\n"
            f"<i>Welcome to the attendance notification system!</i>")
        
        return {'status': 'success', 'linked': True, 'student_id': student.id}
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in start command: {str(e)}")
        bot.send_message(chat_id, "❌ An error occurred while linking your account. Please try again later.")
        return {'status': 'error', 'message': str(e)}

def handle_manual_registration(text, chat_id, school_id, bot):
    """Handle manual registration with school name and student code"""
    try:
        # Expect format: "SCHOOLNAME STUDENTCODE" or "STUDENTCODE SCHOOLNAME"
        parts = [part.strip().upper() for part in text.split()]
        
        if len(parts) < 2:
            bot.send_message(chat_id,
                "❌ Please provide both school name and student code.\n"
                "Example: 'GREENFIELD ABC123' or 'ABC123 GREENFIELD'")
            return {'status': 'error', 'message': 'Insufficient parameters'}
        
        # Try different combinations of school name and student code
        for i in range(len(parts)):
            for j in range(len(parts)):
                if i != j:
                    potential_code = parts[i]
                    potential_school = parts[j]
                    
                    # Find student by code and check if school name matches
                    student = Student.query.join(School).filter(
                        Student.code == potential_code,
                        Student.school_id == school_id,
                        func.upper(School.name).contains(potential_school)
                    ).first()
                    
                    if student:
                        # Check if already linked to another chat
                        if student.telegram_chat_id and student.telegram_chat_id != chat_id:
                            bot.send_message(chat_id,
                                f"⚠️ This student code is already linked to another account.\n"
                                f"Student: {student.first_name} {student.last_name}")
                            return {'status': 'error', 'message': 'Already linked'}
                        
                        # Update student's telegram info
                        student.telegram_chat_id = chat_id
                        student.telegram_status = True
                        db.session.commit()
                        
                        # Send confirmation message
                        bot.send_message(chat_id,
                            f"✅ <b>Successfully linked!</b>\n\n"
                            f"👤 <b>Student:</b> {student.first_name} {student.last_name}\n"
                            f"🏫 <b>School:</b> {student.school.name}\n"
                            f"📚 <b>Grade:</b> {student.grade_level}\n\n"
                            f"You will now receive attendance notifications.")
                        
                        return {'status': 'success', 'linked': True, 'student_id': student.id}
        
        # If no match found
        bot.send_message(chat_id,
            "❌ No matching student found. Please check:\n"
            "• Your school name is correct\n"
            "• Your student code is correct\n"
            "• You're using the right school bot\n\n"
            "Format: 'SCHOOL_NAME STUDENT_CODE'\n"
            "Example: 'GREENFIELD ABC123'")
        
        return {'status': 'error', 'message': 'No matching student found'}
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in manual registration: {str(e)}")
        bot.send_message(chat_id, "❌ An error occurred. Please try again later.")
        return {'status': 'error', 'message': str(e)}

def send_help_message(chat_id, school_id, bot):
    """Send help message to user"""
    try:
        # Get school information
        school = School.query.get(school_id)
        school_name = school.name if school else "the school"
        
        help_text = (
            f"👋 <b>Welcome to {school_name} Attendance Bot!</b>\n\n"
            f"To link your account, you can:\n\n"
            f"1️⃣ <b>Use invitation link</b>\n"
            f"   Click the link provided by your school\n\n"
            f"2️⃣ <b>Manual registration</b>\n"
            f"   Send your school name and student code\n"
            f"   Example: 'GREENFIELD ABC123'\n\n"
            f"📝 <b>Need help?</b>\n"
            f"Contact your school administrator for:\n"
            f"• Your student code\n"
            f"• Invitation link\n"
            f"• Technical support"
        )
        
        bot.send_message(chat_id, help_text)
        return {'status': 'ok', 'message': 'Help sent'}
        
    except Exception as e:
        print(f"Error sending help: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def send_attendance_notification(student_id, message, notification_type='info'):
    """Send attendance notification to a specific student"""
    try:
        student = Student.query.get(student_id)
        if not student or not student.telegram_status or not student.telegram_chat_id:
            return False
        
        # Get global bot configuration (active bot)
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return False
        
        bot = TelegramBot(bot_config.bot_token, student.school_id)
        
        # Format message based on type
        if notification_type == 'absent':
            emoji = '🔴'
            title = 'ABSENCE NOTIFICATION'
        elif notification_type == 'present':
            emoji = '✅'
            title = 'ATTENDANCE CONFIRMED'
        elif notification_type == 'late':
            emoji = '⏰'
            title = 'LATE ARRIVAL'
        else:
            emoji = 'ℹ️'
            title = 'ATTENDANCE UPDATE'
        
        formatted_message = (
            f"{emoji} <b>{title}</b>\n\n"
            f"👤 <b>Student:</b> {student.first_name} {student.last_name}\n"
            f"🏫 <b>School:</b> {student.school.name}\n"
            f"📅 <b>Date:</b> {message}\n\n"
            f"<i>This is an automated notification from your school's attendance system.</i>"
        )
        
        return bot.send_message(student.telegram_chat_id, formatted_message)
        
    except Exception as e:
        print(f"Error sending attendance notification: {str(e)}")
        return False

def broadcast_message_to_school(school_id, message, grade_level=None, section_id=None):
    """Broadcast a message to all connected students in a school"""
    try:
        # Build query
        query = Student.query.filter_by(
            school_id=school_id,
            telegram_status=True
        ).filter(Student.telegram_chat_id.isnot(None))
        
        # Filter by grade level if specified
        if grade_level:
            query = query.filter_by(grade_level=grade_level)
        
        # Filter by section if specified
        if section_id:
            query = query.filter_by(section_id=section_id)
        
        students = query.all()
        
        if not students:
            return {'status': 'error', 'message': 'No connected students found'}
        
        # Get global bot configuration (active bot)
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return {'status': 'error', 'message': 'No active bot configuration found'}
        
        bot = TelegramBot(bot_config.bot_token, school_id)
        
        # Send to all students
        sent_count = 0
        failed_count = 0
        
        for student in students:
            try:
                formatted_message = (
                    f"📢 <b>SCHOOL ANNOUNCEMENT</b>\n\n"
                    f"👤 <b>Dear {student.first_name},</b>\n\n"
                    f"{message}\n\n"
                    f"<i>From: {student.school.name}</i>"
                )
                
                if bot.send_message(student.telegram_chat_id, formatted_message):
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Failed to send to student {student.id}: {str(e)}")
                failed_count += 1
        
        return {
            'status': 'success',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_students': len(students)
        }
        
    except Exception as e:
        print(f"Error broadcasting message: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# Example usage functions
def setup_webhook_for_school(school_id, webhook_url):
    """Setup webhook for a school's bot"""
    try:
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return {'status': 'error', 'message': 'No active bot configuration found'}
        
        bot = TelegramBot(bot_config.bot_token, school_id)
        result = bot.set_webhook(webhook_url)
        
        if result and result.get('ok'):
            return {'status': 'success', 'result': result}
        else:
            return {'status': 'error', 'message': 'Failed to set webhook', 'result': result}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def test_bot_connection(school_id):
    """Test if bot is properly configured and responsive"""
    try:
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            return {'status': 'error', 'message': 'No active bot configuration found'}
        
        bot = TelegramBot(bot_config.bot_token, school_id)
        bot_info = bot.get_bot_info()
        
        if bot_info and bot_info.get('ok'):
            return {
                'status': 'success',
                'bot_info': bot_info['result'],
                'message': 'Bot is working correctly'
            }
        else:
            return {'status': 'error', 'message': 'Bot is not responding or token is invalid'}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def send_attendance_notification(student_id, subject_name, date, status, start_time, end_time, school_id):
    """Send attendance notification to student via Telegram"""
    try:
        # Get student information including telegram_chat_id
        student = Student.query.get(student_id)
        if not student or not student.telegram_chat_id:
            print(f"Student {student_id} not found or no telegram_chat_id")
            return False
        
        # Get global bot configuration (active bot)
        bot_config = TelegramConfig.query.filter_by(is_active=True).first()
        if not bot_config:
            print(f"No active bot configuration found")
            return False
        
        bot = TelegramBot(bot_config.bot_token, school_id)
        
        # Create attendance notification message
        status_emoji = {
            'Present': '✅',
            'Absent': '❌',
            'Late': '🕐',
            'Excused': '📝'
        }
        
        emoji = status_emoji.get(status, '📝')
        student_name = f"{student.first_name} {student.last_name}"
        
        message = f"""
📚 <b>Attendance Notification</b>

👤 <b>Name:</b> {student_name}
📖 <b>Subject:</b> {subject_name}
📅 <b>Date:</b> {date}
🕐 <b>Time:</b> {start_time} - {end_time}
{emoji} <b>Status:</b> {status}

---
This is an automated message from your school attendance system.
        """.strip()
        
        # Send the message
        success = bot.send_message(student.telegram_chat_id, message, parse_mode='HTML')
        
        if success:
            print(f"Attendance notification sent to {student_name} (ID: {student_id})")
        else:
            print(f"Failed to send notification to {student_name} (ID: {student_id})")
            
        return success
        
    except Exception as e:
        print(f"Error sending attendance notification: {str(e)}")
        return False
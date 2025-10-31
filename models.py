from database import db
import datetime


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_code = db.Column(db.String(20), unique=True, nullable=False)  # Added school code
    address = db.Column(db.String(255))
    contact = db.Column(db.String(50))

    instructors = db.relationship('Instructor', backref='school', lazy=True)
    school_admins = db.relationship('SchoolAdmin', backref='school', lazy=True)
    sections = db.relationship('Section', backref='school', lazy=True)
    subjects = db.relationship('Subject', backref='school', lazy=True)
    students = db.relationship('Student', backref='school', lazy=True)
    school_instructor_accounts = db.relationship('SchoolInstructorAccount', backref='school', lazy=True)

class MainAdmin(db.Model):
    __tablename__ = 'main_admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class SchoolAdmin(db.Model):
    __tablename__ = 'school_admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    role = db.Column(db.String(50), nullable=False)

    created_instructor_accounts = db.relationship('SchoolInstructorAccount', backref='school_admin', lazy=True)

class Instructor(db.Model):
    __tablename__ = 'instructors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('school_admin.id'))

    schedules = db.relationship('InstructorSchedule', backref='instructor', lazy=True)
    attendances = db.relationship('Attendance', backref='instructor', lazy=True)
    section_advisers = db.relationship('SectionAdviser', backref='instructor', lazy=True)
    school_instructor_accounts = db.relationship('SchoolInstructorAccount', backref='instructor', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    parent_contact = db.Column(db.String(100))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    code = db.Column(db.String(100))
    telegram_chat_id = db.Column(db.String(100), nullable=True, default=None)
    telegram_status = db.Column(db.Boolean, nullable=False, default=False)

    attendances = db.relationship('Attendance', backref='student', lazy=True)
    notifications = db.relationship('Notification', backref='student', lazy=True)

class ParentAccount(db.Model):
    __tablename__ = 'parent_accounts'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('parent_account', uselist=False))
    school = db.relationship('School')

class Section(db.Model):
    __tablename__ = 'sections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    grade_level = db.Column(db.String(100), nullable=False)

    students = db.relationship('Student', backref='section', lazy=True)
    schedules = db.relationship('InstructorSchedule', backref='section', lazy=True)
    section_advisers = db.relationship('SectionAdviser', backref='section', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "grade_level": self.grade_level,
            "school_id": self.school_id
        }


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
    grade_level = db.Column(db.String(100), nullable=False)

    attendances = db.relationship('Attendance', backref='subject', lazy=True)
    schedules = db.relationship('InstructorSchedule', backref='subject', lazy=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    date = db.Column(db.Date)
    status = db.Column(db.Enum('Present','Absent','Late','Excused'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    type = db.Column(db.Enum('SMS','Email'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.Enum('Sent','Failed','Pending'), default='Pending')
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class InstructorSchedule(db.Model):
    __tablename__ = 'instructor_sched'
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(20), nullable=False)

class SchoolInstructorAccount(db.Model):
    __tablename__ = 'school_instructor_account'
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=False)
    school_admin_id = db.Column(db.Integer, db.ForeignKey('school_admin.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    password = db.Column(db.String(255), nullable=True)  # Password for instructor login
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class SectionAdviser(db.Model):
    __tablename__ = 'section_adviser'
    section_adviser_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    instructor_id = db.Column('intsructor_id', db.Integer, db.ForeignKey('instructors.id'), nullable=False)


class TelegramConfig(db.Model):
    __tablename__ = 'telegram_config'

    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(255), nullable=False)
    bot_username = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "bot_token": self.bot_token,
            "bot_username": self.bot_username,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)  # ID of the user who performed the action
    username = db.Column(db.String(100), nullable=False)  # Username of the user who performed the action
    user_role = db.Column(db.String(50), nullable=False)  # Role: school_admin, instructor, etc.
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    entity_type = db.Column(db.String(50), nullable=False)  # student, instructor, subject, section, account, etc.
    entity_id = db.Column(db.Integer, nullable=True)  # ID of the affected entity
    entity_name = db.Column(db.String(255), nullable=True)  # Name/description of the affected entity
    description = db.Column(db.Text, nullable=True)  # Detailed description of the action
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address
    user_agent = db.Column(db.Text, nullable=True)  # User's browser/device info
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "school_id": self.school_id,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "description": self.description,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


# Messaging Models for Mobile App
class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    participant1_id = db.Column(db.Integer, nullable=False)  # User ID from SchoolInstructorAccount or Student
    participant1_type = db.Column(db.String(20), nullable=False)  # 'instructor', 'student', 'admin'
    participant2_id = db.Column(db.Integer, nullable=False)
    participant2_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    school = db.relationship('School', backref='conversations')
    
    def get_participant_info(self, participant_id, participant_type):
        """Get participant name and details"""
        if participant_type == 'instructor':
            account = SchoolInstructorAccount.query.get(participant_id)
            if account and account.instructor:
                return {
                    'id': account.id,
                    'name': account.instructor.name,
                    'role': 'instructor',
                    'email': account.instructor.email
                }
        elif participant_type == 'parent':
            from models import ParentAccount, Student as StudentModel
            parent = ParentAccount.query.get(participant_id)
            if parent:
                s = StudentModel.query.get(parent.student_id)
                display = f"Parent of {s.first_name} {s.last_name}" if s else 'Parent'
                return {
                    'id': parent.id,
                    'name': display,
                    'role': 'parent',
                    'email': None
                }
        elif participant_type == 'student':
            student = Student.query.get(participant_id)
            if student:
                return {
                    'id': student.id,
                    'name': student.name,
                    'role': 'student',
                    'email': student.email if hasattr(student, 'email') else None
                }
        elif participant_type == 'admin':
            admin = SchoolAdmin.query.get(participant_id)
            if admin:
                return {
                    'id': admin.id,
                    'name': admin.username,
                    'role': 'school_admin',
                    'email': None
                }
        return None
    
    def to_dict(self, current_user_id, current_user_type):
        """Convert to dictionary for API response"""
        # Determine the other participant
        if self.participant1_id == current_user_id and self.participant1_type == current_user_type:
            other_id = self.participant2_id
            other_type = self.participant2_type
        else:
            other_id = self.participant1_id
            other_type = self.participant1_type
        
        other_participant = self.get_participant_info(other_id, other_type)
        
        # Get last message
        last_msg = self.messages.order_by(Message.timestamp.desc()).first()
        
        # Count unread messages for current user
        unread_count = self.messages.filter(
            Message.receiver_id == current_user_id,
            Message.receiver_type == current_user_type,
            Message.is_read == False
        ).count()
        
        return {
            'id': self.id,
            'participantId': other_participant['id'] if other_participant else 0,
            'participantName': other_participant['name'] if other_participant else 'Unknown',
            'participantRole': other_participant['role'] if other_participant else 'unknown',
            'lastMessage': last_msg.content if last_msg else None,
            'lastMessageTime': last_msg.timestamp.isoformat() if last_msg else None,
            'unreadCount': unread_count,
            'avatar': None
        }


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'instructor', 'student', 'admin'
    receiver_id = db.Column(db.Integer, nullable=False)
    receiver_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(50), default='text')  # 'text', 'announcement', 'notification'
    
    def get_sender_info(self):
        """Get sender details"""
        if self.sender_type == 'instructor':
            account = SchoolInstructorAccount.query.get(self.sender_id)
            if account and account.instructor:
                return {
                    'name': account.instructor.name,
                    'role': 'instructor'
                }
        elif self.sender_type == 'parent':
            from models import ParentAccount, Student as StudentModel
            parent = ParentAccount.query.get(self.sender_id)
            if parent:
                s = StudentModel.query.get(parent.student_id)
                display = f"Parent of {s.first_name} {s.last_name}" if s else 'Parent'
                return {
                    'name': display,
                    'role': 'parent'
                }
        elif self.sender_type == 'student':
            student = Student.query.get(self.sender_id)
            if student:
                return {
                    'name': student.name,
                    'role': 'student'
                }
        elif self.sender_type == 'admin':
            admin = SchoolAdmin.query.get(self.sender_id)
            if admin:
                return {
                    'name': admin.username,
                    'role': 'school_admin'
                }
        return {'name': 'Unknown', 'role': 'unknown'}
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        sender_info = self.get_sender_info()
        
        return {
            'id': self.id,
            'conversationId': self.conversation_id,
            'senderId': self.sender_id,
            'senderName': sender_info['name'],
            'senderRole': sender_info['role'],
            'receiverId': self.receiver_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'isRead': self.is_read,
            'type': self.message_type
        }



from database import db


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
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
    time = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(20), nullable=False)

class SchoolInstructorAccount(db.Model):
    __tablename__ = 'school_instructor_account'
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=False)
    school_admin_id = db.Column(db.Integer, db.ForeignKey('school_admin.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)

class SectionAdviser(db.Model):
    __tablename__ = 'section_adviser'
    section_adviser_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=False)
    instructor_id = db.Column('intsructor_id', db.Integer, db.ForeignKey('instructors.id'), nullable=False)

class GenCode(db.Model):
    __tablename__ = 'gen_code'
    id = db.Column(db.Integer, primary_key=True)
    gen_code = db.Column(db.String(255), nullable=False)

    



from flask import Blueprint, jsonify
from models import School, Student, Instructor, Subject, Section

school_api = Blueprint('school_api', __name__, url_prefix='/api/schools')

@school_api.route('/<int:school_id>', methods=['GET'])
def get_school(school_id: int):
    school = School.query.get_or_404(school_id)

    # Basic stats (optional, fast counts)
    total_students = Student.query.filter_by(school_id=school_id).count()
    total_instructors = Instructor.query.filter_by(school_id=school_id).count()
    total_subjects = Subject.query.filter_by(school_id=school_id).count()
    total_sections = Section.query.filter_by(school_id=school_id).count()

    return jsonify({
        'id': school.id,
        'name': school.name,
        'schoolCode': school.school_code,
        'address': school.address,
        'contact': school.contact,
        'stats': {
            'students': total_students,
            'instructors': total_instructors,
            'subjects': total_subjects,
            'sections': total_sections
        }
    })

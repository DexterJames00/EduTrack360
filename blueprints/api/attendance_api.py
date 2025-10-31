from flask import Blueprint, jsonify, request
from datetime import date
from models import Attendance, ParentAccount, Student, Subject, Instructor, db
from blueprints.api.auth_api import token_required

attendance_api = Blueprint('attendance_api', __name__, url_prefix='/api/attendance')


def _get_parent_student_id(user_id: int) -> int | None:
    parent = ParentAccount.query.get(user_id)
    return parent.student_id if parent else None


@attendance_api.route('/summary', methods=['GET'])
@token_required
def summary():
    """Return a compact summary of attendance for the current user (parents only).
    Includes today's entries and total counts.
    """
    if request.user_type != 'parent':
        return jsonify({'success': False, 'message': 'Only parents supported for attendance summary for now'}), 403

    student_id = _get_parent_student_id(request.user_id)
    if not student_id:
        return jsonify({'success': False, 'message': 'Student not found for parent'}), 404

    # Today's records
    today = date.today()
    todays = Attendance.query.filter_by(student_id=student_id).filter(Attendance.date == today).all()

    # Totals
    totals_query = db.session.query(Attendance.status, db.func.count(Attendance.id)).\
        filter(Attendance.student_id == student_id).\
        group_by(Attendance.status).all()
    totals = {status: count for status, count in totals_query}

    def serialize_att(a: Attendance):
        subj = Subject.query.get(a.subject_id)
        instr = Instructor.query.get(a.instructor_id)
        return {
            'date': a.date.isoformat() if a.date else None,
            'status': a.status,
            'subject': subj.name if subj else None,
            'instructor': instr.name if instr else None,
        }

    return jsonify({
        'success': True,
        'studentId': student_id,
        'today': [serialize_att(a) for a in todays],
        'totals': totals
    })


@attendance_api.route('/history', methods=['GET'])
@token_required
def history():
    """Return recent attendance history for parent (defaults to last 50)."""
    if request.user_type != 'parent':
        return jsonify({'success': False, 'message': 'Only parents supported for attendance history for now'}), 403

    student_id = _get_parent_student_id(request.user_id)
    if not student_id:
        return jsonify({'success': False, 'message': 'Student not found for parent'}), 404

    limit = request.args.get('limit', 50, type=int)
    rows = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc(), Attendance.id.desc()).limit(limit).all()

    def serialize_att(a: Attendance):
        subj = Subject.query.get(a.subject_id)
        instr = Instructor.query.get(a.instructor_id)
        return {
            'date': a.date.isoformat() if a.date else None,
            'status': a.status,
            'subject': subj.name if subj else None,
            'instructor': instr.name if instr else None,
        }

    return jsonify({'success': True, 'items': [serialize_att(a) for a in rows]})

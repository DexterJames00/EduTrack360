from flask import Blueprint, request, jsonify, render_template, session
from database import db
from models import Section
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

school_admin_bp = Blueprint('crud_section', __name__, url_prefix='/school_admin/api')
# Get all sections for the school
@school_admin_bp.route('/sections', methods=['GET'])
def get_sections():
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

    try:
        sections = Section.query.filter_by(school_id=school_id).all()
        return jsonify({
            "success": True,
            "sections": [section.to_dict() for section in sections]
        })
    except Exception as e:
        print("Error fetching sections:", e)
        return jsonify({"success": False, "message": "Error fetching sections."}), 500


# Create a new section
@school_admin_bp.route('/create/section', methods=['POST'])
def create_section():
    try:
        data = request.get_json()
        if not data.get('name') or not data.get('grade_level'):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        school_id = session.get('school_id')
        if not school_id:
            return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

        # Check if section name already exists in this school
        existing_section = Section.query.filter_by(name=data.get('name'), school_id=school_id).first()
        if existing_section:
            return jsonify({"success": False, "message": f"Section '{data.get('name')}' already exists in your school."}), 400

        new_section = Section(
            name=data.get('name'),
            grade_level=data.get('grade_level'),
            school_id=school_id
        )

        db.session.add(new_section)
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Section created successfully!", 
            "section": new_section.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print("Error creating section:", e)
        return jsonify({"success": False, "message": "Error creating section. Please try again."}), 500 

# Update an existing section
@school_admin_bp.route('/update/section/<int:section_id>', methods=['PUT'])
def update_section(section_id): 
    try:
        data = request.get_json()
        if not data.get('name') or not data.get('grade_level'):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        school_id = session.get('school_id')
        if not school_id:
            return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

        section = Section.query.filter_by(id=section_id, school_id=school_id).first()
        if not section:
            return jsonify({"success": False, "message": "Section not found"}), 404

        # Check if new name conflicts with existing section (excluding current section)
        existing_section = Section.query.filter_by(name=data.get('name'), school_id=school_id).filter(Section.id != section_id).first()
        if existing_section:
            return jsonify({"success": False, "message": f"Section name '{data.get('name')}' already exists in your school."}), 400

        section.name = data.get('name')
        section.grade_level = data.get('grade_level')
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Section updated successfully!", 
            "section": section.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print("Error updating section:", e)
        return jsonify({"success": False, "message": "Error updating section. Please try again."}), 500 

#delete a section (using raw SQL to avoid column mapping issues)
@school_admin_bp.route('/delete/section/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    try:
        print(f"Attempting to delete section with ID: {section_id}")
        
        school_id = session.get('school_id')
        print(f"School ID from session: {school_id}")
        
        if not school_id:
            return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

        section = Section.query.filter_by(id=section_id, school_id=school_id).first()
        print(f"Found section: {section}")
        
        if not section:
            return jsonify({"success": False, "message": "Section not found"}), 404

        # Check for dependencies using raw SQL to avoid column mapping issues
        dependencies = []
        
        # Check students using raw SQL
        students_result = db.session.execute(
            text("SELECT COUNT(*) as count FROM students WHERE section_id = :section_id"), 
            {"section_id": section_id}
        ).fetchone()
        students_count = students_result[0] if students_result else 0
        print(f"Students count: {students_count}")
        if students_count > 0:
            dependencies.append(f"{students_count} student(s)")
        
        # Check schedules using raw SQL
        schedules_result = db.session.execute(
            text("SELECT COUNT(*) as count FROM instructor_sched WHERE section_id = :section_id"), 
            {"section_id": section_id}
        ).fetchone()
        schedules_count = schedules_result[0] if schedules_result else 0
        print(f"Schedules count: {schedules_count}")
        if schedules_count > 0:
            dependencies.append(f"{schedules_count} schedule(s)")
            
        # Check section advisers using raw SQL
        advisers_result = db.session.execute(
            text("SELECT COUNT(*) as count FROM section_adviser WHERE section_id = :section_id"), 
            {"section_id": section_id}
        ).fetchone()
        advisers_count = advisers_result[0] if advisers_result else 0
        print(f"Section advisers count: {advisers_count}")
        if advisers_count > 0:
            dependencies.append(f"{advisers_count} section adviser(s)")

        if dependencies:
            return jsonify({
                "success": False, 
                "message": f"Cannot delete section '{section.name}' because it has {', '.join(dependencies)} assigned to it. Please remove these assignments first."
            }), 400

        print(f"No dependencies found, proceeding to delete section '{section.name}'")
        
        # Use raw SQL to delete the section to avoid triggering relationship queries
        db.session.execute(
            text("DELETE FROM sections WHERE id = :section_id"), 
            {"section_id": section_id}
        )
        db.session.commit()
        print("Section deleted successfully")

        return jsonify({"success": True, "message": "Section deleted successfully!"})
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"Error deleting section - Type: {error_type}, Message: {error_msg}")
        
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        # Return user-friendly error message
        return jsonify({
            "success": False, 
            "message": "Error deleting section. Please try again."
        }), 500
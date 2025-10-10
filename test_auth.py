#!/usr/bin/env python3
"""
Test script to verify the updated authentication system
"""

from app import app
from database import db
from models import SchoolAdmin, SchoolInstructorAccount, Instructor, School
from werkzeug.security import check_password_hash

def test_auth_system():
    with app.app_context():
        print("🧪 Testing Authentication System")
        print("=" * 50)
        
        # Test School Admins
        print("\n📋 SCHOOL ADMIN ACCOUNTS:")
        school_admins = SchoolAdmin.query.all()
        for admin in school_admins:
            print(f"  • ID: {admin.id}")
            print(f"    Username: {admin.username}")
            print(f"    School ID: {admin.school_id}")
            print(f"    Role: {admin.role}")
            print(f"    Password Hash: {admin.password[:20]}...")
            print()
        
        # Test Instructor Accounts
        print("\n👨‍🏫 INSTRUCTOR ACCOUNTS:")
        instructor_accounts = SchoolInstructorAccount.query.all()
        for account in instructor_accounts:
            instructor = account.instructor
            print(f"  • Account ID: {account.id}")
            print(f"    Instructor: {instructor.name if instructor else 'None'}")
            print(f"    Email: {instructor.email if instructor else 'None'}")
            print(f"    School ID: {account.school_id}")
            print(f"    Has Password: {'Yes' if account.password else 'No'}")
            if account.password:
                print(f"    Password Hash: {account.password[:20]}...")
            print()
        
        # Test Password Verification
        print("\n🔑 PASSWORD VERIFICATION TESTS:")
        
        # Test admin password
        if school_admins:
            admin = school_admins[0]
            test_password = "admin123"  # Assuming this is what you used
            is_valid = check_password_hash(admin.password, test_password)
            print(f"  • Admin '{admin.username}' with password '{test_password}': {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test instructor password
        if instructor_accounts:
            account = instructor_accounts[0]
            if account.password:
                test_password = "instructor123"  # The default we set
                is_valid = check_password_hash(account.password, test_password)
                instructor_name = account.instructor.name if account.instructor else 'Unknown'
                print(f"  • Instructor '{instructor_name}' with password '{test_password}': {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        print("\n✅ Authentication system test complete!")

if __name__ == "__main__":
    test_auth_system()
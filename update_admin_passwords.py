#!/usr/bin/env python3
"""
Update school admin passwords to be properly hashed
"""

from app import app
from database import db
from models import SchoolAdmin
from werkzeug.security import generate_password_hash

def update_admin_passwords():
    with app.app_context():
        try:
            # Find admins with plain text passwords
            admins = SchoolAdmin.query.all()
            updated_count = 0
            
            for admin in admins:
                # Check if password is not hashed
                if not (admin.password.startswith('scrypt:') or admin.password.startswith('pbkdf2:')):
                    print(f"Updating password for admin: {admin.username}")
                    print(f"  Old password (plain): {admin.password}")
                    
                    # Hash the existing password
                    admin.password = generate_password_hash(admin.password)
                    print(f"  New password (hashed): {admin.password[:30]}...")
                    updated_count += 1
            
            db.session.commit()
            print(f"\n✅ Updated {updated_count} admin account(s) with hashed passwords")
            
            # Show all admin accounts
            print("\n📋 All School Admin Accounts:")
            for admin in admins:
                print(f"  • {admin.username} (School: {admin.school_id})")
                print(f"    Password type: {'Hashed' if admin.password.startswith(('scrypt:', 'pbkdf2:')) else 'Plain text'}")
            
        except Exception as e:
            print(f"❌ Error updating admin passwords: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_admin_passwords()
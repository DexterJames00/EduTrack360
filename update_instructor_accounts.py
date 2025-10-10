#!/usr/bin/env python3
"""
Update script to add password column to school_instructor_account table
and set default passwords for existing accounts
"""

from app import app
from database import db
from models import SchoolInstructorAccount
from werkzeug.security import generate_password_hash

def update_instructor_accounts():
    with app.app_context():
        try:
            # Add the password column if it doesn't exist
            with db.engine.connect() as conn:
                try:
                    conn.execute(db.text("""
                        ALTER TABLE school_instructor_account 
                        ADD COLUMN password VARCHAR(255);
                    """))
                    print("✅ Added password column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("ℹ️  Password column already exists")
                    else:
                        print(f"⚠️  Error adding password column: {e}")
                
                try:
                    conn.execute(db.text("""
                        ALTER TABLE school_instructor_account 
                        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    """))
                    print("✅ Added created_at column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("ℹ️  Created_at column already exists")
                    else:
                        print(f"⚠️  Error adding created_at column: {e}")
                
                conn.commit()
            
            # Update existing accounts that don't have passwords
            accounts_without_password = SchoolInstructorAccount.query.filter(
                (SchoolInstructorAccount.password == None) | (SchoolInstructorAccount.password == '')
            ).all()
            
            for account in accounts_without_password:
                # Set a default password (you should change this)
                default_password = "instructor123"
                account.password = generate_password_hash(default_password)
                print(f"Set default password for instructor account ID {account.id}")
            
            db.session.commit()
            print(f"✅ Updated {len(accounts_without_password)} instructor accounts with default passwords")
            print("⚠️  Default password is 'instructor123' - make sure to change it!")
            
        except Exception as e:
            print(f"❌ Error updating instructor accounts: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_instructor_accounts()
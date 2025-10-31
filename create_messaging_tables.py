"""
Database migration script to add Conversation and Message tables for mobile app messaging
Run this script to create the new tables without affecting existing data
"""

from database import db
from app_realtime import app
from models import Conversation, Message, ParentAccount

def create_messaging_tables():
    """Create the messaging tables if they don't exist"""
    with app.app_context():
        try:
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'conversations' not in existing_tables:
                print("Creating conversations table...")
                Conversation.__table__.create(db.engine)
                print("✓ Conversations table created successfully")
            else:
                print("✓ Conversations table already exists")
            
            if 'messages' not in existing_tables:
                print("Creating messages table...")
                Message.__table__.create(db.engine)
                print("✓ Messages table created successfully")
            else:
                print("✓ Messages table already exists")

            if 'parent_accounts' not in existing_tables:
                print("Creating parent_accounts table...")
                ParentAccount.__table__.create(db.engine)
                print("✓ Parent accounts table created successfully")
            else:
                print("✓ Parent accounts table already exists")
            
            print("\n✅ Database migration completed successfully!")
            print("\nNew tables ensured:")
            print("- conversations: Stores chat conversations between users")
            print("- messages: Stores individual messages in conversations")
            print("- parent_accounts: Parents linked to students for app login")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    print("=== EduTrack360 Mobile App Database Migration ===\n")
    print("This will create the messaging tables for the mobile app.")
    print("Existing data will NOT be affected.\n")
    
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = create_messaging_tables()
        if success:
            print("\n🎉 Migration complete! You can now use the mobile app messaging features.")
        else:
            print("\n⚠️ Migration failed. Please check the error messages above.")
    else:
        print("\nMigration cancelled.")

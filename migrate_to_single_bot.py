#!/usr/bin/env python3
"""
Migration script to update database for single bot system
- Add school_code to schools table
- Remove school_id from telegram_config
- Add is_active to telegram_config
- Keep only one active bot configuration
"""

import sys
sys.path.append('.')

from app_clean import app
from database import db
from models import School, TelegramConfig
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        print("🔄 Starting database migration...")
        
        try:
            # Add school_code column to schools table if it doesn't exist
            print("📝 Adding school_code column to schools table...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE schools ADD COLUMN school_code VARCHAR(20) UNIQUE"))
                    conn.commit()
                print("✅ Added school_code column")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("ℹ️  school_code column already exists")
                else:
                    print(f"⚠️  Error adding school_code: {e}")
            
            # Update existing schools with default codes
            print("📝 Updating schools with default codes...")
            try:
                with db.engine.connect() as conn:
                    # Get schools without codes
                    result = conn.execute(text("SELECT id, name FROM schools WHERE school_code IS NULL OR school_code = ''"))
                    schools_to_update = result.fetchall()
                    
                    for school in schools_to_update:
                        school_id, school_name = school
                        # Generate a default code based on school name
                        code = ''.join([c.upper() for c in school_name if c.isalnum()])[:10]
                        if not code:
                            code = f"SCHOOL{school_id}"
                        
                        # Make sure code is unique
                        check_result = conn.execute(text("SELECT id FROM schools WHERE school_code = :code AND id != :id"), 
                                                  {"code": code, "id": school_id})
                        if check_result.fetchone():
                            code = f"{code}{school_id}"
                        
                        # Update the school
                        conn.execute(text("UPDATE schools SET school_code = :code WHERE id = :id"), 
                                   {"code": code, "id": school_id})
                        print(f"   - {school_name} -> {code}")
                    
                    conn.commit()
            except Exception as e:
                print(f"⚠️  Error updating school codes: {e}")
            
            print("✅ Updated school codes")
            
            # Add is_active column to telegram_config if it doesn't exist
            print("📝 Adding is_active column to telegram_config table...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE telegram_config ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                    conn.commit()
                print("✅ Added is_active column")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("ℹ️  is_active column already exists")
                else:
                    print(f"⚠️  Error adding is_active: {e}")
            
            # Update existing telegram configs
            print("📝 Updating telegram configurations...")
            try:
                with db.engine.connect() as conn:
                    # Get all configs
                    result = conn.execute(text("SELECT id, bot_username FROM telegram_config ORDER BY id"))
                    configs = result.fetchall()
                    
                    if configs:
                        # Keep the first config as active, deactivate others
                        first_id, first_username = configs[0]
                        conn.execute(text("UPDATE telegram_config SET is_active = TRUE WHERE id = :id"), {"id": first_id})
                        
                        for config_id, username in configs[1:]:
                            conn.execute(text("UPDATE telegram_config SET is_active = FALSE WHERE id = :id"), {"id": config_id})
                        
                        conn.commit()
                        
                        print(f"✅ Set @{first_username} as active bot")
                        if len(configs) > 1:
                            print(f"ℹ️  Deactivated {len(configs) - 1} other bot(s)")
            except Exception as e:
                print(f"⚠️  Error updating telegram configs: {e}")
            
            # Try to remove school_id column from telegram_config
            print("📝 Attempting to remove school_id column from telegram_config...")
            try:
                with db.engine.connect() as conn:
                    # First remove any foreign key constraints
                    try:
                        conn.execute(text("ALTER TABLE telegram_config DROP FOREIGN KEY telegram_config_ibfk_1"))
                    except:
                        pass
                    
                    conn.execute(text("ALTER TABLE telegram_config DROP COLUMN school_id"))
                    conn.commit()
                print("✅ Removed school_id column")
            except Exception as e:
                print(f"⚠️  Could not remove school_id column: {e}")
                print("ℹ️  This is okay - the column will be ignored")
            
            print("\n" + "="*50)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*50)
            
            # Show current status
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT name, school_code FROM schools"))
                    schools = result.fetchall()
                    print(f"📊 Schools with codes:")
                    for name, code in schools:
                        print(f"   - {name} ({code})")
                    
                    result = conn.execute(text("SELECT bot_username FROM telegram_config WHERE is_active = TRUE"))
                    active_bot = result.fetchone()
                    if active_bot:
                        print(f"\n🤖 Active bot: @{active_bot[0]}")
                    else:
                        print("\n⚠️  No active bot found")
            except Exception as e:
                print(f"⚠️  Error showing status: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    if migrate_database():
        print("\n✅ Migration successful! You can now use the single bot system.")
    else:
        print("\n❌ Migration failed! Please check the errors above.")
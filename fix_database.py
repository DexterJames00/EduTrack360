from app import app, db
import pymysql

def fix_database():
    with app.app_context():
        try:
            # Get the database connection
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # Alter the telegram_chat_id column to allow NULL values
            alter_query = """
            ALTER TABLE students 
            MODIFY COLUMN telegram_chat_id VARCHAR(100) NULL
            """
            
            cursor.execute(alter_query)
            connection.commit()
            print("✅ Successfully updated telegram_chat_id column to allow NULL values")
            
            # Also ensure telegram_status has a default value
            alter_status_query = """
            ALTER TABLE students 
            MODIFY COLUMN telegram_status BOOLEAN NOT NULL DEFAULT FALSE
            """
            
            cursor.execute(alter_status_query)
            connection.commit()
            print("✅ Successfully updated telegram_status column with default value")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error fixing database: {e}")

if __name__ == "__main__":
    fix_database()
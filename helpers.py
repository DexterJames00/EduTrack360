from werkzeug.security import check_password_hash

def get_user_by_username(mysql, username):
    """
    Fetch a user record by username.
    Returns a dictionary or None if not found.
    """
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT user_id, username, password, school_id, role FROM users WHERE username = %s",
        (username,)
    )
    user = cursor.fetchone()
    cursor.close()

    if user:
        return {
            "user_id": user[0],
            "username": user[1],
            "password": user[2],
            "school_id": user[3],
            "role": user[4]
        }
    return None


def verify_password(stored_password, entered_password):
    """
    Verify password — supports both plain text and hashed.
    """
    if stored_password.startswith("pbkdf2:"):
        return check_password_hash(stored_password, entered_password)
    return stored_password == entered_password

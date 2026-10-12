"""
CineMithresh - Authentication Helpers
Secure password hashing, user session tracking, and access-control decorators.
"""

from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database

def hash_password(password: str) -> str:
    """Hash password using Werkzeug's secure pbkdf2:sha256."""
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return check_password_hash(hashed_password, plain_password)

def get_current_user_from_db():
    """Retrieve the currently logged-in user record from database based on session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = Database.query_one("""
        SELECT id, name, email, phone, role, cine_points, created_at
        FROM users WHERE id = %s
    """, (user_id,))
    return user

def login_required(f):
    """Ensure endpoint is only accessible to authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please sign in to proceed.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

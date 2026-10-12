"""
CineMithresh - Authentication Routes
Handles user registration, login, logout, and session state.
"""

from flask import Blueprint, request, jsonify, session
from database import Database
from utils.auth_helpers import hash_password, verify_password, get_current_user_from_db, login_required
from utils.security import is_valid_email, sanitize_string, get_or_create_csrf_token, csrf_protect

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/csrf', methods=['GET'])
def get_csrf():
    """Return CSRF token for the active session."""
    token = get_or_create_csrf_token()
    return jsonify({
        'success': True,
        'csrf_token': token
    })

@auth_bp.route('/register', methods=['POST'])
@csrf_protect
def register():
    data = request.get_json(silent=True) or request.form.to_dict()
    name = sanitize_string(data.get('name', ''))
    email = sanitize_string(data.get('email', '')).lower()
    password = data.get('password', '')
    phone = sanitize_string(data.get('phone', ''))

    if not name:
        return jsonify({'success': False, 'error': 'Full name is required.'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Please provide a valid email address.'}), 400
    if not password or len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters long.'}), 400

    # Enforce unique email constraint
    existing = Database.query_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({'success': False, 'error': 'An account with this email address already exists. Please sign in.'}), 409

    hashed_pw = hash_password(password)

    try:
        res = Database.execute("""
            INSERT INTO users (name, email, password_hash, phone, role, cine_points)
            VALUES (%s, %s, %s, %s, 'customer', 100)
        """, (name, email, hashed_pw, phone))
        user_id = res['lastrowid']

        # Store in session (secure cookie)
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        session.permanent = True

        # Legacy CGI compatibility table update
        try:
            Database.execute("INSERT INTO login_page (UserName, Email, Password) VALUES (%s, %s, %s)",
                             (name, email, '[HASHED_PROTECTED]'))
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'user': {
                'id': user_id,
                'name': name,
                'email': email,
                'phone': phone,
                'role': 'customer',
                'cine_points': 100
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to create account: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
@csrf_protect
def login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = sanitize_string(data.get('email', '')).lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required.'}), 400

    user = Database.query_one("SELECT * FROM users WHERE email = %s", (email,))
    if not user or not verify_password(password, user['password_hash']):
        return jsonify({'success': False, 'error': 'Invalid email or password. Please try again.'}), 401

    # Set session
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_name'] = user['name']
    session.permanent = True

    return jsonify({
        'success': True,
        'message': f'Welcome back, {user["name"]}!',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user.get('phone', ''),
            'role': user.get('role', 'customer'),
            'cine_points': user.get('cine_points', 450)
        }
    })

@auth_bp.route('/demo-login', methods=['POST'])
@csrf_protect
def demo_login():
    """Quick demo test login as Mithresh P."""
    user = Database.query_one("SELECT * FROM users WHERE email = %s", ('mithresh@cinemithresh.com',))
    if not user:
        return jsonify({'success': False, 'error': 'Demo user not found.'}), 404

    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_name'] = user['name']
    session.permanent = True

    return jsonify({
        'success': True,
        'message': f'Logged in as demo user {user["name"]}',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user.get('phone', ''),
            'role': user.get('role', 'admin'),
            'cine_points': user.get('cine_points', 500)
        }
    })

@auth_bp.route('/logout', methods=['POST'])
@csrf_protect
def logout():
    csrf_token = session.get('csrf_token')
    session.clear()
    if csrf_token:
        session['csrf_token'] = csrf_token
    else:
        get_or_create_csrf_token()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully.',
        'csrf_token': session.get('csrf_token')
    })

@auth_bp.route('/me', methods=['GET'])
def me():
    """Return currently authenticated user from session."""
    user = get_current_user_from_db()
    if not user:
        return jsonify({'success': True, 'authenticated': False, 'user': None})

    # Count user's confirmed bookings
    bookings_count = Database.query_one("""
        SELECT COUNT(*) as count FROM bookings WHERE user_id = %s OR customer_email = %s
    """, (user['id'], user['email']))

    return jsonify({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user.get('phone', ''),
            'role': user.get('role', 'customer'),
            'cine_points': user.get('cine_points', 450),
            'bookings_count': bookings_count['count'] if bookings_count else 0
        }
    })

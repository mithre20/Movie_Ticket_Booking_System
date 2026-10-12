"""
CineMithresh - Security Helpers
Provides CSRF protection, input validation, and sanitization.
"""

import os
import re
import secrets
import hmac
import hashlib
from flask import session, request, jsonify
from functools import wraps
from config import Config

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def get_or_create_csrf_token() -> str:
    """Generate or retrieve existing CSRF token stored in secure session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token: str) -> bool:
    """Verify CSRF token against session."""
    expected = session.get('csrf_token')
    if not expected or not token:
        return False
    return secrets.compare_digest(expected, token)

def csrf_protect(f):
    """Decorator to enforce CSRF token validation on state-changing requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Allow token from headers (X-CSRF-Token) or JSON body
            token = request.headers.get('X-CSRF-Token')
            if not token and request.is_json:
                token = request.get_json(silent=True, force=True).get('csrf_token')
            if not token:
                token = request.form.get('csrf_token')

            if not token or not validate_csrf_token(token):
                return jsonify({
                    'success': False,
                    'error': 'Invalid or missing CSRF token. Please refresh and try again.'
                }), 403
        return f(*args, **kwargs)
    return decorated_function

def is_valid_email(email: str) -> bool:
    if not email or len(email) > 150:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def sanitize_string(val: str, max_len: int = 255) -> str:
    if not val:
        return ''
    return val.strip()[:max_len]

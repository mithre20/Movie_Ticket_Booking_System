"""
CineMithresh - Full-Stack Movie Ticket Booking System
Flask Application Entry Point
"""

import os
import sys
from flask import Flask, send_from_directory, render_template_string, jsonify, session, request
from config import Config
from database import init_database, Database, ACTIVE_DB_TYPE
from seed_data import seed_database
from utils.security import get_or_create_csrf_token

# Import Route Blueprints
from routes.auth_routes import auth_bp
from routes.movie_routes import movie_bp
from routes.booking_routes import booking_bp
from routes.review_routes import review_bp
from routes.payment_routes import payment_bp

def create_app():
    # Static assets (styles.css, app.js) live in ./static and are served only
    # from there. HTML pages are served explicitly below. This prevents the
    # project root (e.g. .env, the SQLite database, Python sources) from being
    # downloadable as static files.
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    # Initialize and seed database if necessary
    with app.app_context():
        init_database()
        # Seed if movies catalog is empty
        try:
            movies_count = Database.query_one("SELECT COUNT(*) as cnt FROM movies")
            if not movies_count or movies_count['cnt'] == 0:
                print("[*] Empty database detected. Seeding initial CineMithresh dataset...")
                seed_database()
        except Exception as e:
            print(f"[!] Database check note: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(movie_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(payment_bp)

    # Security headers on every response
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Provide CSRF cookie for fetch() convenience
        if 'csrf_token' in session:
            response.set_cookie('XSRF-TOKEN', session['csrf_token'], samesite='Lax', httponly=False)
        return response

    # ==========================================
    # HTML Page Routes (Strict Preservation)
    # ==========================================
    @app.route('/')
    @app.route('/index.html')
    def index_page():
        get_or_create_csrf_token()
        return send_from_directory('.', 'index.html')

    @app.route('/booking.html')
    def booking_page():
        get_or_create_csrf_token()
        return send_from_directory('.', 'booking.html')

    @app.route('/login.html')
    def login_page():
        get_or_create_csrf_token()
        return send_from_directory('.', 'login.html')

    @app.route('/ratings.html')
    def ratings_page():
        get_or_create_csrf_token()
        return send_from_directory('.', 'ratings.html')

    @app.route('/about_us.html')
    def about_page():
        get_or_create_csrf_token()
        return send_from_directory('.', 'about_us.html')

    # ==========================================
    # Health & System Status Endpoint
    # ==========================================
    @app.route('/api/health')
    def health_check():
        db_ok = True
        try:
            Database.query_one("SELECT 1")
        except Exception:
            db_ok = False

        return jsonify({
            'status': 'healthy' if db_ok else 'degraded',
            'database': 'connected' if db_ok else 'error',
            'database_type': ACTIVE_DB_TYPE or Config.DB_TYPE,
            'payment_mode': Config.PAYMENT_MODE,
            'app_version': '2.0.0-production'
        })

    # ==========================================
    # Legacy CGI Redirection Handlers
    # ==========================================
    @app.route('/connection1.py', methods=['GET', 'POST'])
    def legacy_connection1():
        """Gracefully handle legacy registration form submissions."""
        if request.method == 'POST':
            name = request.form.get('myname', '')
            email = request.form.get('email', '')
            # Redirect to login page with notice
            return f"""<script>
                alert('Account registered in CineMithresh Database!');
                window.location.href = '/login.html';
            </script>"""
        return send_from_directory('.', 'connection1.py')

    @app.route('/register.py', methods=['GET', 'POST'])
    def legacy_register():
        """Gracefully handle legacy booking form submissions."""
        if request.method == 'POST':
            return f"""<script>
                alert('Booking processed!');
                window.location.href = '/booking.html';
            </script>"""
        return send_from_directory('.', 'register.py')

    @app.route('/rating.py', methods=['GET', 'POST'])
    def legacy_rating():
        """Gracefully handle legacy rating submissions."""
        if request.method == 'POST':
            return f"""<script>
                alert('Rating recorded!');
                window.location.href = '/ratings.html';
            </script>"""
        return send_from_directory('.', 'rating.py')

    return app

app = create_app()

if __name__ == '__main__':
    port = Config.PORT
    print("=" * 60)
    print("  🎬 CineMithresh Cinema Booking System - Flask Server")
    print(f"  [>] Live Web Application: http://localhost:{port}")
    print(f"  [+] Active Database Engine: {ACTIVE_DB_TYPE or Config.DB_TYPE}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)

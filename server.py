#!/usr/bin/env python3
"""
CineMithresh - Full-Stack Movie Ticket Booking Server
Launches the Flask backend server with MySQL database connectivity and API endpoints.

Usage:
    python server.py
    or
    python app.py
"""

import os
import sys
from app import app
from config import Config
from database import ACTIVE_DB_TYPE

def run_server():
    # Ensure Windows console handles utf-8 if supported
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    port = Config.PORT
    db_engine = ACTIVE_DB_TYPE or Config.DB_TYPE

    print("=" * 64)
    print("  🎬 CineMithresh - Premium Movie Ticket Booking System")
    print(f"  [>] Server running live at: http://localhost:{port}")
    print(f"  [+] Active Database Engine: {db_engine.upper()}")
    print(f"  [+] Payment Mode: {Config.PAYMENT_MODE.upper()} SANDBOX")
    print(f"  [+] All Pages & API Endpoints Active")
    print("  Press Ctrl+C to stop the server")
    print("=" * 64)

    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)

if __name__ == '__main__':
    run_server()

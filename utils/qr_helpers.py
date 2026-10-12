"""
CineMithresh - Ticket QR Code & Verifiable Token Helpers
Generates and validates cryptographically signed tokens for movie admissions.
"""

import hmac
import hashlib
import time
from config import Config

def generate_ticket_token(booking_ref: str, show_id: int, seats_str: str) -> str:
    """Generate an HMAC-SHA256 authenticated QR token for a confirmed ticket."""
    payload = f"{booking_ref}:{show_id}:{seats_str}:{Config.SECRET_KEY}"
    signature = hmac.new(
        Config.SECRET_KEY.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()[:24]
    return f"TKT-{booking_ref}-{signature}"

def verify_ticket_token(token: str, booking_ref: str, show_id: int, seats_str: str) -> bool:
    """Verify that a QR code token matches the issued signature."""
    expected = generate_ticket_token(booking_ref, show_id, seats_str)
    return hmac.compare_digest(token, expected)

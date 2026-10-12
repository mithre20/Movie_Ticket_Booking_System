"""
CineMithresh - Payment Routes
Handles sandbox / test-mode payment gateway intents and server-side verification.
Never processes or stores sensitive credit/debit card numbers or CVVs.
"""

import hmac
import hashlib
import secrets
import time
from flask import Blueprint, request, jsonify
from config import Config
from utils.security import csrf_protect

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payment_bp.route('/config', methods=['GET'])
def payment_config():
    """Return public payment gateway settings for checkout UI."""
    return jsonify({
        'success': True,
        'mode': Config.PAYMENT_MODE,
        'merchant_name': Config.PAYMENT_MERCHANT,
        'currency': Config.PAYMENT_CURRENCY,
        'notice': 'Test Sandbox Mode Active — No real charges will be made.'
    })

@payment_bp.route('/create-intent', methods=['POST'])
@csrf_protect
def create_payment_intent():
    """
    Generate a server-verified checkout payment order intent.
    Never accepts or handles raw credit card or CVV details.
    """
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('amount', 0.0))
    except (ValueError, TypeError):
        amount = 0.0

    if amount <= 0:
        return jsonify({'success': False, 'error': 'Invalid payment amount.'}), 400

    order_id = f"ORDER-{secrets.randbelow(900000) + 100000}"
    timestamp = int(time.time())
    
    # Generate cryptographic signature for this transaction intent
    sig_payload = f"{order_id}:{amount}:{Config.PAYMENT_CURRENCY}:{timestamp}"
    signature = hmac.new(
        Config.SECRET_KEY.encode('utf-8'),
        sig_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return jsonify({
        'success': True,
        'mode': 'SANDBOX_TEST_GATEWAY',
        'order_id': order_id,
        'amount': amount,
        'currency': Config.PAYMENT_CURRENCY,
        'merchant': Config.PAYMENT_MERCHANT,
        'timestamp': timestamp,
        'signature': signature,
        'label': 'CineMithresh Instant UPI / Card Sandbox Gateway'
    })

@payment_bp.route('/verify', methods=['POST'])
@csrf_protect
def verify_payment():
    """
    Server-side verification of payment intent.
    Confirms valid signature and generates server proof of payment.
    """
    data = request.get_json(silent=True) or {}
    order_id = data.get('order_id', '')
    amount = float(data.get('amount', 0.0))
    timestamp = int(data.get('timestamp', 0))
    provided_signature = data.get('signature', '')
    simulated_outcome = data.get('simulated_outcome', 'success')  # allow testing failure scenarios!

    if simulated_outcome == 'failure':
        return jsonify({
            'success': False,
            'verified': False,
            'error': 'Payment declined by test bank simulator. Please try again.'
        }), 402

    # Verify cryptographic signature
    expected_payload = f"{order_id}:{amount}:{Config.PAYMENT_CURRENCY}:{timestamp}"
    expected_sig = hmac.new(
        Config.SECRET_KEY.encode('utf-8'),
        expected_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(provided_signature, expected_sig):
        return jsonify({
            'success': False,
            'verified': False,
            'error': 'Invalid payment signature. Transaction rejected.'
        }), 400

    txn_id = f"TXN-SANDBOX-{secrets.token_hex(8).upper()}"

    return jsonify({
        'success': True,
        'verified': True,
        'transaction_id': txn_id,
        'order_id': order_id,
        'status': 'SUCCESS',
        'message': 'Payment authorized and verified successfully in sandbox mode.'
    })

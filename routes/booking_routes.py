"""
CineMithresh - Booking Routes
Handles seat availability, temporary holds with TTL, pricing calculations,
concurrency-safe atomic reservations, ticket history, and QR verification.
"""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from database import Database
from config import Config
from utils.security import is_valid_email, sanitize_string, csrf_protect
from utils.qr_helpers import generate_ticket_token, verify_ticket_token

booking_bp = Blueprint('booking', __name__, url_prefix='/api')

def cleanup_expired_holds():
    """Remove expired seat holds from the database."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        Database.execute("DELETE FROM seat_holds WHERE expires_at <= %s", (now_str,))
    except Exception:
        pass

@booking_bp.route('/shows/<int:show_id>/seats', methods=['GET'])
def get_seats_for_show(show_id):
    """
    Retrieve real seat availability for a given show.
    Returns whether each seat is available, booked, held by someone else, or held by current session.
    """
    cleanup_expired_holds()

    show = Database.query_one("SELECT id, movie_id, screen_id, show_date, show_time FROM shows WHERE id = %s", (show_id,))
    if not show:
        return jsonify({'success': False, 'error': 'Show not found.'}), 404

    current_session_id = request.headers.get('X-Session-ID') or session.get('client_session_id', '')

    # 1. All seat definitions
    seats = Database.query_all("SELECT * FROM seat_definitions ORDER BY row_label ASC, seat_number ASC")

    # 2. Confirmed booked seats
    booked_rows = Database.query_all("SELECT seat_id FROM booked_seats WHERE show_id = %s", (show_id,))
    booked_set = {r['seat_id'] for r in booked_rows}

    # 3. Active seat holds
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    holds_rows = Database.query_all("SELECT seat_id, session_id FROM seat_holds WHERE show_id = %s AND expires_at > %s", (show_id, now_str))
    holds_dict = {h['seat_id']: h['session_id'] for h in holds_rows}

    seat_list = []
    for s in seats:
        s_id = s['id']
        if s_id in booked_set:
            status = 'booked'
        elif s_id in holds_dict:
            status = 'held_by_me' if (current_session_id and holds_dict[s_id] == current_session_id) else 'held'
        else:
            status = 'available'

        seat_list.append({
            'id': s['id'],
            'row': s['row_label'],
            'number': s['seat_number'],
            'tier': s['tier'],
            'price': float(s['price']),
            'is_vip': bool(s['is_vip']),
            'status': status
        })

    return jsonify({
        'success': True,
        'show': show,
        'seats': seat_list,
        'total_seats': len(seat_list),
        'booked_count': len(booked_set),
        'held_count': len(holds_dict)
    })

@booking_bp.route('/shows/<int:show_id>/hold-seats', methods=['POST'])
@csrf_protect
def hold_seats(show_id):
    """
    Hold seats temporarily (TTL = 5 mins) while user confirms checkout.
    Prevents race condition and double bookings.
    """
    cleanup_expired_holds()

    data = request.get_json(silent=True) or {}
    requested_seats = data.get('seats', [])
    client_session_id = request.headers.get('X-Session-ID') or data.get('session_id') or session.get('client_session_id')
    if not client_session_id:
        client_session_id = secrets.token_hex(16)
        session['client_session_id'] = client_session_id

    if not requested_seats or not isinstance(requested_seats, list):
        return jsonify({'success': False, 'error': 'Please select at least 1 seat.'}), 400

    if len(requested_seats) > 8:
        return jsonify({'success': False, 'error': 'Maximum 8 tickets allowed per booking.'}), 400

    user_id = session.get('user_id')
    now = datetime.now()
    expires_at = (now + timedelta(seconds=Config.SEAT_HOLD_TTL_SECONDS)).strftime('%Y-%m-%d %H:%M:%S')

    with Database.transaction() as tx:
        # Check if any requested seat is already booked
        for seat_id in requested_seats:
            booked = tx.query_one("SELECT id FROM booked_seats WHERE show_id = %s AND seat_id = %s", (show_id, seat_id))
            if booked:
                return jsonify({
                    'success': False,
                    'error': f'Seat {seat_id} was just booked by another customer.'
                }), 409

            # Check if held by another session
            held = tx.query_one("""
                SELECT session_id FROM seat_holds 
                WHERE show_id = %s AND seat_id = %s AND expires_at > %s
            """, (show_id, seat_id, now.strftime('%Y-%m-%d %H:%M:%S')))
            if held and held['session_id'] != client_session_id:
                return jsonify({
                    'success': False,
                    'error': f'Seat {seat_id} is currently being held by another moviegoer. Please select another seat.'
                }), 409

        # Release existing holds for this session that aren't in requested_seats
        tx.execute("DELETE FROM seat_holds WHERE show_id = %s AND session_id = %s", (show_id, client_session_id))

        # Insert fresh holds
        for seat_id in requested_seats:
            tx.execute("""
                INSERT INTO seat_holds (show_id, seat_id, session_id, user_id, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (show_id, seat_id, client_session_id, user_id, expires_at))

    return jsonify({
        'success': True,
        'message': f'Seats held for {Config.SEAT_HOLD_TTL_SECONDS // 60} minutes.',
        'held_seats': requested_seats,
        'session_id': client_session_id,
        'expires_at': expires_at
    })

@booking_bp.route('/shows/<int:show_id>/release-seats', methods=['POST'])
@csrf_protect
def release_seats(show_id):
    """Release seat hold for the current session."""
    client_session_id = request.headers.get('X-Session-ID') or request.get_json(silent=True, force=True).get('session_id') or session.get('client_session_id')
    if client_session_id:
        Database.execute("DELETE FROM seat_holds WHERE show_id = %s AND session_id = %s", (show_id, client_session_id))
    return jsonify({'success': True, 'message': 'Held seats released.'})

@booking_bp.route('/booking/calculate-summary', methods=['POST'])
def calculate_summary():
    """
    Authoritative server-side pricing calculation.
    Calculates tickets subtotal, snacks subtotal, fees, coupon discount, and grand total.
    """
    data = request.get_json(silent=True) or {}
    seats_list = data.get('seats', [])
    snacks_dict = data.get('snacks', {})
    promo_code = sanitize_string(data.get('promo_code', '')).upper()

    # 1. Calculate tickets subtotal from DB prices
    ticket_subtotal = 0.0
    seat_details = []
    if seats_list:
        placeholders = ','.join(['%s'] * len(seats_list))
        rows = Database.query_all(f"SELECT id, tier, price FROM seat_definitions WHERE id IN ({placeholders})", tuple(seats_list))
        for r in rows:
            price = float(r['price'])
            ticket_subtotal += price
            seat_details.append({
                'id': r['id'],
                'tier': r['tier'],
                'price': price
            })

    # 2. Calculate snacks subtotal from DB snacks table
    snacks_subtotal = 0.0
    snack_items = []
    if snacks_dict and isinstance(snacks_dict, dict):
        for snack_id, qty in snacks_dict.items():
            try:
                qty_int = int(qty)
            except (ValueError, TypeError):
                qty_int = 0
            if qty_int > 0:
                snack_row = Database.query_one("SELECT id, name, price FROM snacks WHERE id = %s", (snack_id,))
                if snack_row:
                    item_price = float(snack_row['price'])
                    item_sub = item_price * qty_int
                    snacks_subtotal += item_sub
                    snack_items.append({
                        'id': snack_row['id'],
                        'name': snack_row['name'],
                        'quantity': qty_int,
                        'price': item_price,
                        'subtotal': item_sub
                    })

    # 3. Convenience fee
    convenience_fee = 30.0 if len(seats_list) > 0 else 0.0

    total_before_discount = ticket_subtotal + snacks_subtotal + convenience_fee
    discount_amount = 0.0
    discount_percent = 0.0
    coupon_valid = False
    coupon_message = ''

    # 4. Coupon validation
    if promo_code:
        coupon = Database.query_one("SELECT * FROM coupons WHERE code = %s AND is_active = 1", (promo_code,))
        if coupon and total_before_discount > 0:
            discount_percent = float(coupon['discount_percent'])
            discount_amount = round(total_before_discount * (discount_percent / 100.0), 2)
            coupon_valid = True
            coupon_message = f'Promo code {promo_code} applied! {int(discount_percent)}% discount activated.'
        else:
            coupon_valid = False
            coupon_message = 'Invalid or expired coupon code.'

    grand_total = max(0.0, total_before_discount - discount_amount)

    return jsonify({
        'success': True,
        'ticket_subtotal': ticket_subtotal,
        'snacks_subtotal': snacks_subtotal,
        'convenience_fee': convenience_fee,
        'total_before_discount': total_before_discount,
        'discount_amount': discount_amount,
        'discount_percent': discount_percent,
        'grand_total': grand_total,
        'coupon_valid': coupon_valid,
        'coupon_message': coupon_message,
        'seats': seat_details,
        'snacks': snack_items
    })

@booking_bp.route('/booking/confirm', methods=['POST'])
@csrf_protect
def confirm_booking():
    """
    Atomic transaction to finalize movie ticket booking.
    Verifies seats availability, records payment verification, saves booking & seats,
    cleans up holds, generates unique booking ref and digital QR pass.
    """
    data = request.get_json(silent=True) or {}
    show_id = data.get('show_id')
    seats_list = data.get('seats', [])
    snacks_dict = data.get('snacks', {})
    promo_code = sanitize_string(data.get('promo_code', '')).upper()
    name = sanitize_string(data.get('customer_name', ''))
    email = sanitize_string(data.get('customer_email', '')).lower()
    phone = sanitize_string(data.get('customer_phone', ''))
    payment_method = sanitize_string(data.get('payment_method', 'TEST_SANDBOX_GATEWAY'))
    payment_ref = sanitize_string(data.get('payment_ref', ''))

    if not show_id:
        return jsonify({'success': False, 'error': 'Show ID is required.'}), 400
    if not seats_list:
        return jsonify({'success': False, 'error': 'Please select at least 1 seat.'}), 400
    if not name:
        return jsonify({'success': False, 'error': 'Customer name is required.'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Valid email address is required.'}), 400

    show = Database.query_one("""
        SELECT s.id, s.movie_id, s.screen_id, s.show_date, s.show_time,
               m.title as movie_title, m.poster, sc.name as screen_name
        FROM shows s
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        WHERE s.id = %s
    """, (show_id,))
    if not show:
        return jsonify({'success': False, 'error': 'Show not found.'}), 404

    # Generate unique booking reference
    booking_ref = f"MB-{secrets.randbelow(900000) + 100000}"
    qr_token = generate_ticket_token(booking_ref, show_id, ','.join(sorted(seats_list)))
    user_id = session.get('user_id')

    # Atomic Reservation
    try:
        with Database.transaction() as tx:
            # 1. Double check seat conflicts inside transaction
            for seat_id in seats_list:
                already_booked = tx.query_one("""
                    SELECT id FROM booked_seats WHERE show_id = %s AND seat_id = %s
                """, (show_id, seat_id))
                if already_booked:
                    return jsonify({
                        'success': False,
                        'error': f'Seat {seat_id} is already reserved by another customer. Please choose other seats.'
                    }), 409

            # 2. Server-calculated totals
            ticket_subtotal = 0.0
            seat_rows = []
            for seat_id in seats_list:
                s_def = tx.query_one("SELECT id, tier, price FROM seat_definitions WHERE id = %s", (seat_id,))
                if not s_def:
                    return jsonify({'success': False, 'error': f'Invalid seat identifier: {seat_id}'}), 400
                p = float(s_def['price'])
                ticket_subtotal += p
                seat_rows.append(s_def)

            snacks_subtotal = 0.0
            snack_rows = []
            if snacks_dict and isinstance(snacks_dict, dict):
                for sn_id, qty in snacks_dict.items():
                    qty_int = int(qty) if str(qty).isdigit() else 0
                    if qty_int > 0:
                        s_item = tx.query_one("SELECT id, name, price FROM snacks WHERE id = %s", (sn_id,))
                        if s_item:
                            sub = float(s_item['price']) * qty_int
                            snacks_subtotal += sub
                            snack_rows.append((s_item['id'], qty_int, float(s_item['price']), sub))

            convenience_fee = 30.0
            total_before = ticket_subtotal + snacks_subtotal + convenience_fee
            discount_amount = 0.0

            if promo_code:
                c = tx.query_one("SELECT discount_percent FROM coupons WHERE code = %s AND is_active = 1", (promo_code,))
                if c:
                    discount_amount = round(total_before * (float(c['discount_percent']) / 100.0), 2)

            grand_total = max(0.0, total_before - discount_amount)

            # 3. Insert Booking Master Record
            res = tx.execute("""
                INSERT INTO bookings (
                    booking_ref, user_id, show_id, customer_name, customer_email, customer_phone,
                    ticket_subtotal, snacks_subtotal, convenience_fee, discount_amount, promo_code,
                    total_amount, payment_status, payment_method, payment_ref, qr_token
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                booking_ref, user_id, show_id, name, email, phone,
                ticket_subtotal, snacks_subtotal, convenience_fee, discount_amount, promo_code or None,
                grand_total, 'completed', payment_method, payment_ref or f"PAY-TEST-{secrets.token_hex(6).upper()}", qr_token
            ))
            booking_id = res.lastrowid

            # 4. Insert Booked Seats
            for s_def in seat_rows:
                tx.execute("""
                    INSERT INTO booked_seats (booking_id, show_id, seat_id, price, tier)
                    VALUES (%s, %s, %s, %s, %s)
                """, (booking_id, show_id, s_def['id'], float(s_def['price']), s_def['tier']))

            # 5. Insert Booking Snacks
            for sn_id, qty, p_item, sub in snack_rows:
                tx.execute("""
                    INSERT INTO booking_snacks (booking_id, snack_id, quantity, price_per_item, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (booking_id, sn_id, qty, p_item, sub))

            # 6. Remove any holds
            for seat_id in seats_list:
                tx.execute("DELETE FROM seat_holds WHERE show_id = %s AND seat_id = %s", (show_id, seat_id))

            # 7. Update user loyalty points if authenticated
            if user_id:
                tx.execute("UPDATE users SET cine_points = cine_points + 50 WHERE id = %s", (user_id,))

            # 8. Legacy CGI table compatibility insert
            try:
                tx.execute("INSERT INTO booking (Movie, Seats) VALUES (%s, %s)",
                           (show['movie_title'], f"{len(seats_list)} Seats ({', '.join(seats_list)})"))
            except Exception:
                pass

        return jsonify({
            'success': True,
            'message': 'Booking successfully confirmed!',
            'booking': {
                'id': booking_id,
                'booking_ref': booking_ref,
                'movie_title': show['movie_title'],
                'poster': show['poster'],
                'screen': show['screen_name'],
                'show_date': show['show_date'],
                'show_time': show['show_time'],
                'seats': seats_list,
                'seat_count': len(seats_list),
                'total_amount': grand_total,
                'customer_name': name,
                'customer_email': email,
                'qr_token': qr_token,
                'booked_at': datetime.now().isoformat()
            }
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to process booking: {str(e)}'}), 500

@booking_bp.route('/bookings/my-tickets', methods=['GET'])
def get_my_tickets():
    """Retrieve booking history for the logged-in user or requested email."""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    query_email = request.args.get('email', '').strip().lower()

    if not user_id and not query_email:
        return jsonify({'success': True, 'bookings': []})

    target_email = user_email or query_email

    sql = """
        SELECT b.id, b.booking_ref, b.customer_name, b.customer_email,
               b.ticket_subtotal, b.snacks_subtotal, b.convenience_fee, b.discount_amount,
               b.total_amount, b.payment_status, b.qr_token, b.created_at,
               s.show_date, s.show_time, m.title as movie_title, m.poster, sc.name as screen_name
        FROM bookings b
        JOIN shows s ON b.show_id = s.id
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        WHERE (b.user_id = %s OR LOWER(b.customer_email) = %s)
        ORDER BY b.created_at DESC LIMIT 20
    """
    bookings = Database.query_all(sql, (user_id or -1, target_email))

    result = []
    for b in bookings:
        # Fetch seats for this booking
        seat_rows = Database.query_all("SELECT seat_id FROM booked_seats WHERE booking_id = %s", (b['id'],))
        seats = [r['seat_id'] for r in seat_rows]

        result.append({
            'bookingId': b['booking_ref'],
            'movieTitle': b['movie_title'],
            'poster': b['poster'],
            'theater': b['screen_name'],
            'showDate': b['show_date'],
            'showTime': b['show_time'],
            'seats': seats,
            'seatCount': len(seats),
            'totalAmount': float(b['total_amount']),
            'customerName': b['customer_name'],
            'customerEmail': b['customer_email'],
            'qrToken': b['qr_token'],
            'paymentStatus': b['payment_status'],
            'bookedAt': b['created_at']
        })

    return jsonify({'success': True, 'bookings': result})

@booking_bp.route('/tickets/<booking_ref>', methods=['GET'])
def get_ticket_detail(booking_ref):
    """Retrieve single ticket detail by booking reference."""
    booking = Database.query_one("""
        SELECT b.*, s.show_date, s.show_time, m.title as movie_title, m.poster, sc.name as screen_name
        FROM bookings b
        JOIN shows s ON b.show_id = s.id
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        WHERE b.booking_ref = %s
    """, (booking_ref,))
    if not booking:
        return jsonify({'success': False, 'error': 'Ticket not found.'}), 404

    seat_rows = Database.query_all("SELECT seat_id, tier, price FROM booked_seats WHERE booking_id = %s", (booking['id'],))
    seats = [r['seat_id'] for r in seat_rows]

    return jsonify({
        'success': True,
        'ticket': {
            'bookingId': booking['booking_ref'],
            'movieTitle': booking['movie_title'],
            'poster': booking['poster'],
            'theater': booking['screen_name'],
            'showDate': booking['show_date'],
            'showTime': booking['show_time'],
            'seats': seats,
            'seatCount': len(seats),
            'totalAmount': float(booking['total_amount']),
            'customerName': booking['customer_name'],
            'customerEmail': booking['customer_email'],
            'qrToken': booking['qr_token'],
            'paymentStatus': booking['payment_status'],
            'bookedAt': booking['created_at']
        }
    })

@booking_bp.route('/tickets/verify/<qr_token>', methods=['GET'])
def verify_qr_pass(qr_token):
    """
    Gate usher verification endpoint for scanning admission passes.
    Validates QR token and returns booking verification record.
    """
    booking = Database.query_one("""
        SELECT b.id, b.booking_ref, b.show_id, b.customer_name, b.customer_email,
               b.total_amount, b.payment_status, b.created_at,
               s.show_date, s.show_time, m.title as movie_title, sc.name as screen_name
        FROM bookings b
        JOIN shows s ON b.show_id = s.id
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        WHERE b.qr_token = %s
    """, (qr_token,))

    if not booking:
        return jsonify({
            'success': False,
            'verified': False,
            'error': 'Invalid or fraudulent ticket pass. Admission denied.'
        }), 404

    seat_rows = Database.query_all("SELECT seat_id FROM booked_seats WHERE booking_id = %s", (booking['id'],))
    seats = [r['seat_id'] for r in seat_rows]

    return jsonify({
        'success': True,
        'verified': True,
        'message': 'Valid CineMithresh M-Ticket Pass. Admission Granted.',
        'ticket': {
            'booking_ref': booking['booking_ref'],
            'movie_title': booking['movie_title'],
            'screen': booking['screen_name'],
            'show_date': booking['show_date'],
            'show_time': booking['show_time'],
            'seats': seats,
            'customer_name': booking['customer_name'],
            'payment_status': booking['payment_status']
        }
    })

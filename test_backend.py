"""
CineMithresh - Comprehensive Backend Automated Test Suite
Tests authentication, sessions, CSRF, movie catalog, seat holds,
concurrency conflicts, price calculations, test payment gateway,
booking transactions, QR verification, and reviews.
"""

import unittest
import json
from app import create_app
from database import Database

class TestCineMithreshBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def get_csrf(self, client):
        """Helper to get a valid CSRF token from active session."""
        res = client.get('/api/auth/csrf')
        data = res.get_json()
        return data.get('csrf_token', '')

    def test_01_health_check(self):
        """Test health endpoint."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')

    def test_02_authentication_workflow(self):
        """Test registration, duplicate email rejection, login, and logout."""
        c = self.app.test_client()
        csrf = self.get_csrf(c)

        test_email = 'test_cine_user@example.com'
        # Clean up if existing
        Database.execute("DELETE FROM users WHERE email = %s", (test_email,))

        # 1. Register
        reg_payload = {
            'name': 'Test Cinegoer',
            'email': test_email,
            'password': 'SecurePassword@123',
            'phone': '9876543210'
        }
        res = c.post('/api/auth/register', json=reg_payload, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], test_email)

        # 2. Duplicate registration attempt should fail with 409
        res_dup = c.post('/api/auth/register', json=reg_payload, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_dup.status_code, 409)

        # 3. Check /me session
        res_me = c.get('/api/auth/me')
        data_me = res_me.get_json()
        self.assertTrue(data_me['authenticated'])
        self.assertEqual(data_me['user']['email'], test_email)

        # 4. Logout
        res_logout = c.post('/api/auth/logout', headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_logout.status_code, 200)

        # 5. /me after logout
        res_me2 = c.get('/api/auth/me')
        self.assertFalse(res_me2.get_json()['authenticated'])

        # 6. Invalid password login should fail
        res_fail = c.post('/api/auth/login', json={'email': test_email, 'password': 'WrongPassword!'}, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_fail.status_code, 401)

        # 7. Valid password login should succeed
        res_login = c.post('/api/auth/login', json={'email': test_email, 'password': 'SecurePassword@123'}, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_login.status_code, 200)
        self.assertTrue(res_login.get_json()['success'])

    def test_03_movies_catalog(self):
        """Test movie list, search, and details."""
        res = self.client.get('/api/movies')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['movies']), 15)

        # Search query
        res_search = self.client.get('/api/movies?q=Pushpa')
        data_search = res_search.get_json()
        self.assertTrue(len(data_search['movies']) >= 1)
        self.assertIn('Pushpa', data_search['movies'][0]['title'])

        # Single movie detail
        res_detail = self.client.get('/api/movies/pushpa-2')
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.get_json()['movie']['id'], 'pushpa-2')

    def test_04_seat_availability_and_holds(self):
        """Test real seat availability, temporary holding, and conflict rejection."""
        c1 = self.app.test_client()
        csrf1 = self.get_csrf(c1)
        c2 = self.app.test_client()
        csrf2 = self.get_csrf(c2)

        # Get first show
        shows = Database.query_all("SELECT id FROM shows LIMIT 1")
        self.assertTrue(len(shows) > 0)
        show_id = shows[0]['id']

        # Get seat status
        res_seats = c1.get(f'/api/shows/{show_id}/seats')
        self.assertEqual(res_seats.status_code, 200)
        seats_data = res_seats.get_json()
        self.assertEqual(seats_data['total_seats'], 80)

        # Client 1 holds seat 'C4'
        hold_payload = {'seats': ['C4'], 'session_id': 'session-client-1'}
        res_hold1 = c1.post(f'/api/shows/{show_id}/hold-seats', json=hold_payload,
                            headers={'X-CSRF-Token': csrf1, 'X-Session-ID': 'session-client-1'})
        self.assertEqual(res_hold1.status_code, 200)
        self.assertTrue(res_hold1.get_json()['success'])

        # Client 2 attempts to hold the same seat 'C4' -> MUST FAIL with 409 Conflict
        res_hold2 = c2.post(f'/api/shows/{show_id}/hold-seats', json=hold_payload,
                            headers={'X-CSRF-Token': csrf2, 'X-Session-ID': 'session-client-2'})
        self.assertEqual(res_hold2.status_code, 409)
        self.assertIn('held by another moviegoer', res_hold2.get_json()['error'])

        # Release hold
        c1.post(f'/api/shows/{show_id}/release-seats', json={'session_id': 'session-client-1'},
                headers={'X-CSRF-Token': csrf1, 'X-Session-ID': 'session-client-1'})

    def test_05_price_calculation_and_coupons(self):
        """Test server-side price calculation and 20% coupon discount."""
        payload = {
            'seats': ['A1', 'C1'],  # VIP (350) + Platinum (220) = 570
            'snacks': {'popcorn': 1, 'coke': 1},  # Popcorn (180) + Coke (90) = 270
            'promo_code': 'MITHRESH20'  # 20% discount
        }
        res = self.client.post('/api/booking/calculate-summary', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['ticket_subtotal'], 570.0)
        self.assertEqual(data['snacks_subtotal'], 270.0)
        self.assertEqual(data['convenience_fee'], 30.0)
        # Total before = 570 + 270 + 30 = 870
        self.assertEqual(data['total_before_discount'], 870.0)
        # 20% of 870 = 174.0
        self.assertEqual(data['discount_amount'], 174.0)
        # Grand total = 870 - 174 = 696.0
        self.assertEqual(data['grand_total'], 696.0)
        self.assertTrue(data['coupon_valid'])

    def test_06_payment_intent_and_booking_confirmation(self):
        """Test end-to-end sandbox payment and atomic booking creation with QR pass."""
        c = self.app.test_client()
        csrf = self.get_csrf(c)

        # 1. Create Payment Intent
        intent_res = c.post('/api/payments/create-intent', json={'amount': 696.0}, headers={'X-CSRF-Token': csrf})
        self.assertEqual(intent_res.status_code, 200)
        intent_data = intent_res.get_json()
        self.assertTrue(intent_data['success'])

        # 2. Verify Payment (simulated success)
        verify_res = c.post('/api/payments/verify', json={
            'order_id': intent_data['order_id'],
            'amount': intent_data['amount'],
            'timestamp': intent_data['timestamp'],
            'signature': intent_data['signature'],
            'simulated_outcome': 'success'
        }, headers={'X-CSRF-Token': csrf})
        self.assertEqual(verify_res.status_code, 200)
        txn_id = verify_res.get_json()['transaction_id']

        # 3. Confirm Booking
        shows = Database.query_all("SELECT id FROM shows LIMIT 1")
        show_id = shows[0]['id']

        # Pick unique seats for test
        test_seats = ['H9', 'H10']
        # Clean up any previous test booking on these seats
        Database.execute("DELETE FROM booked_seats WHERE show_id = %s AND seat_id IN ('H9', 'H10')", (show_id,))

        booking_payload = {
            'show_id': show_id,
            'seats': test_seats,
            'snacks': {'popcorn': 1},
            'promo_code': 'MITHRESH20',
            'customer_name': 'Mithresh Test Customer',
            'customer_email': 'mithresh_test@cinemithresh.com',
            'customer_phone': '+91 99440 12345',
            'payment_method': 'SANDBOX_UPI',
            'payment_ref': txn_id
        }
        res_book = c.post('/api/booking/confirm', json=booking_payload, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_book.status_code, 201)
        book_data = res_book.get_json()
        self.assertTrue(book_data['success'])
        booking_ref = book_data['booking']['booking_ref']
        qr_token = book_data['booking']['qr_token']
        self.assertTrue(booking_ref.startswith('MB-'))
        self.assertTrue(qr_token.startswith('TKT-'))

        # 4. Immediate duplicate booking attempt on the same seats MUST FAIL with 409 Conflict
        res_dup = c.post('/api/booking/confirm', json=booking_payload, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_dup.status_code, 409)

        # 5. Lookup Ticket by QR Token
        res_qr = c.get(f'/api/tickets/verify/{qr_token}')
        self.assertEqual(res_qr.status_code, 200)
        qr_data = res_qr.get_json()
        self.assertTrue(qr_data['verified'])
        self.assertEqual(qr_data['ticket']['booking_ref'], booking_ref)

        # 6. Lookup in my-tickets
        res_my = c.get('/api/bookings/my-tickets?email=mithresh_test@cinemithresh.com')
        self.assertEqual(res_my.status_code, 200)
        self.assertGreaterEqual(len(res_my.get_json()['bookings']), 1)

    def test_07_reviews_persistence_and_validation(self):
        """Test review submission, input validation, and like counter."""
        c = self.app.test_client()
        csrf = self.get_csrf(c)

        # Invalid rating > 5 should fail
        res_invalid = c.post('/api/reviews', json={
            'movie_id': 'pushpa-2',
            'name': 'Critic John',
            'email': 'john@example.com',
            'rating': 10,
            'comment': 'Good movie!'
        }, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_invalid.status_code, 400)

        # Valid review
        res_valid = c.post('/api/reviews', json={
            'movie_id': 'pushpa-2',
            'name': 'Critic John',
            'email': 'john@example.com',
            'rating': 5,
            'comment': 'Phenomenal action and unmatched Dolby Atmos sound mixing!'
        }, headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_valid.status_code, 201)
        rev_id = res_valid.get_json()['review']['id']

        # Like review
        res_like = c.post(f'/api/reviews/{rev_id}/like', headers={'X-CSRF-Token': csrf})
        self.assertEqual(res_like.status_code, 200)
        self.assertEqual(res_like.get_json()['new_likes'], 1)

if __name__ == '__main__':
    unittest.main()

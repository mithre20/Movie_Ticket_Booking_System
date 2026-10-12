"""
CineMithresh - Reviews & Ratings Routes
Persists audience reviews in database with validation, ratings distribution, and likes.
"""

import time
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database import Database
from utils.security import is_valid_email, sanitize_string, csrf_protect

review_bp = Blueprint('reviews', __name__, url_prefix='/api')

CGI_RATING_MAP = {
    1: 'TOO BAD',
    2: 'BAD',
    3: 'MODRATE',
    4: 'GOOD',
    5: 'EXCELLENT'
}

@review_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """Retrieve audience reviews with optional movie filter and rating statistics."""
    movie_id = request.args.get('movie_id', '').strip()

    sql = """
        SELECT r.id, r.movie_id, r.user_name, r.email, r.rating, r.comment, r.likes,
               DATE(r.created_at) as date, m.title as movie_title
        FROM reviews r
        JOIN movies m ON r.movie_id = m.id
        WHERE 1=1
    """
    params = []
    if movie_id and movie_id != 'all':
        sql += " AND r.movie_id = %s"
        params.append(movie_id)

    sql += " ORDER BY r.created_at DESC"
    reviews = Database.query_all(sql, tuple(params))

    # Calculate overall average rating and distribution
    all_ratings = Database.query_all("SELECT rating FROM reviews")
    total_count = len(all_ratings)
    avg_score = round(sum(r['rating'] for r in all_ratings) / total_count, 1) if total_count > 0 else 5.0

    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in all_ratings:
        v = r['rating']
        if v in counts:
            counts[v] += 1

    distribution = {
        star: {
            'count': count,
            'percent': round((count / total_count * 100), 1) if total_count > 0 else 0
        }
        for star, count in counts.items()
    }

    formatted_reviews = []
    for r in reviews:
        formatted_reviews.append({
            'id': r['id'],
            'movieId': r['movie_id'],
            'movieTitle': r['movie_title'],
            'userName': r['user_name'],
            'email': r['email'],
            'rating': int(r['rating']),
            'date': str(r['date']),
            'comment': r['comment'],
            'likes': int(r.get('likes', 0))
        })

    return jsonify({
        'success': True,
        'count': len(formatted_reviews),
        'total_reviews': total_count,
        'average_score': avg_score,
        'distribution': distribution,
        'reviews': formatted_reviews
    })

@review_bp.route('/reviews', methods=['POST'])
@csrf_protect
def add_review():
    """Submit a verified audience rating & review."""
    data = request.get_json(silent=True) or request.form.to_dict()
    movie_id = sanitize_string(data.get('movie_id') or data.get('movieId', ''))
    name = sanitize_string(data.get('name') or data.get('userName', ''))
    email = sanitize_string(data.get('email', '')).lower()
    comment = sanitize_string(data.get('comment', ''), max_len=1000)

    try:
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        rating = 5

    if not movie_id:
        return jsonify({'success': False, 'error': 'Please select a movie.'}), 400
    if not name:
        return jsonify({'success': False, 'error': 'Name is required.'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Valid email address is required.'}), 400
    if not comment:
        return jsonify({'success': False, 'error': 'Please write a review comment.'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'error': 'Rating must be an integer between 1 and 5.'}), 400

    movie = Database.query_one("SELECT id, title FROM movies WHERE id = %s", (movie_id,))
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found.'}), 404

    review_id = f"rev-{int(time.time() * 1000)}"
    user_id = session.get('user_id')

    try:
        Database.execute("""
            INSERT INTO reviews (id, movie_id, user_id, user_name, email, rating, comment, likes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """, (review_id, movie_id, user_id, name, email, rating, comment))

        # Legacy CGI table compatibility insert
        try:
            cgi_rate_label = CGI_RATING_MAP.get(rating, 'EXCELLENT')
            Database.execute("INSERT INTO ratings (Name, Email, rate) VALUES (%s, %s, %s)",
                             (name, email, cgi_rate_label))
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message': 'Thank you! Your review has been saved to the database.',
            'review': {
                'id': review_id,
                'movieId': movie_id,
                'movieTitle': movie['title'],
                'userName': name,
                'email': email,
                'rating': rating,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'comment': comment,
                'likes': 0
            }
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to save review: {str(e)}'}), 500

@review_bp.route('/reviews/<review_id>/like', methods=['POST'])
@csrf_protect
def like_review(review_id):
    """Increment helpful like counter for a review."""
    rev = Database.query_one("SELECT id, likes FROM reviews WHERE id = %s", (review_id,))
    if not rev:
        return jsonify({'success': False, 'error': 'Review not found.'}), 404

    Database.execute("UPDATE reviews SET likes = likes + 1 WHERE id = %s", (review_id,))
    return jsonify({
        'success': True,
        'new_likes': int(rev.get('likes', 0)) + 1
    })

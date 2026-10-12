"""
CineMithresh - Movie & Cinema Routes
Provides access to movies, theaters, showtimes, and concessions.
"""

from flask import Blueprint, request, jsonify
from database import Database

movie_bp = Blueprint('movies', __name__, url_prefix='/api')

@movie_bp.route('/movies', methods=['GET'])
def get_movies():
    """Retrieve all movies with optional genre filter or search query."""
    genre = request.args.get('genre', '').strip()
    query = request.args.get('q', '').strip().lower()

    sql = "SELECT * FROM movies WHERE 1=1"
    params = []

    if genre and genre.lower() != 'all':
        sql += " AND (LOWER(genre) LIKE %s OR LOWER(language) LIKE %s)"
        params.extend([f"%{genre.lower()}%", f"%{genre.lower()}%"])

    if query:
        sql += " AND (LOWER(title) LIKE %s OR LOWER(genre) LIKE %s OR LOWER(language) LIKE %s OR LOWER(movies.cast) LIKE %s)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"])

    sql += " ORDER BY rating DESC, created_at DESC"
    movies = Database.query_all(sql, tuple(params))
    return jsonify({
        'success': True,
        'count': len(movies),
        'movies': movies
    })

@movie_bp.route('/movies/<movie_id>', methods=['GET'])
def get_movie_detail(movie_id):
    """Retrieve detailed movie metadata by ID."""
    movie = Database.query_one("SELECT * FROM movies WHERE id = %s", (movie_id,))
    if not movie:
        return jsonify({'success': False, 'error': 'Movie not found.'}), 404

    # Fetch available screens and show dates for this movie
    shows = Database.query_all("""
        SELECT DISTINCT s.show_date, s.screen_id, sc.name as screen_name
        FROM shows s
        JOIN screens sc ON s.screen_id = sc.id
        WHERE s.movie_id = %s
        ORDER BY s.id ASC
    """, (movie_id,))

    return jsonify({
        'success': True,
        'movie': movie,
        'available_slots': shows
    })

@movie_bp.route('/screens', methods=['GET'])
def get_screens():
    """List all cinema screens."""
    screens = Database.query_all("SELECT * FROM screens ORDER BY id ASC")
    return jsonify({'success': True, 'screens': screens})

@movie_bp.route('/snacks', methods=['GET'])
def get_snacks():
    """List all available snacks and refreshments."""
    snacks = Database.query_all("SELECT * FROM snacks ORDER BY price ASC")
    return jsonify({'success': True, 'snacks': snacks})

@movie_bp.route('/shows', methods=['GET'])
def get_shows():
    """Query showtimes for movie, screen, and date."""
    movie_id = request.args.get('movie_id')
    screen_id = request.args.get('screen_id')
    show_date = request.args.get('date')

    sql = """
        SELECT s.id, s.movie_id, s.screen_id, s.show_date, s.show_time,
               m.title as movie_title, m.poster, sc.name as screen_name
        FROM shows s
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        WHERE 1=1
    """
    params = []
    if movie_id:
        sql += " AND s.movie_id = %s"
        params.append(movie_id)
    if screen_id:
        sql += " AND s.screen_id = %s"
        params.append(screen_id)
    if show_date:
        sql += " AND s.show_date = %s"
        params.append(show_date)

    sql += " ORDER BY s.id ASC LIMIT 50"
    shows = Database.query_all(sql, tuple(params))
    return jsonify({'success': True, 'shows': shows})

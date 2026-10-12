"""
CineMithresh - Database Access Layer
Supports MySQL as primary persistent database with thread-safe pooling & transactional safety.
Includes fallback support for SQLite when local MySQL service is inactive.
"""

import os
import sys
import sqlite3
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

# Track active database type
ACTIVE_DB_TYPE = None

import time
import socket

# Cache MySQL availability to avoid TCP timeout on every query
_MYSQL_CHECK_CACHE = {'available': None, 'last_check': 0}

def is_mysql_reachable() -> bool:
    now = time.time()
    if _MYSQL_CHECK_CACHE['available'] is not None and (now - _MYSQL_CHECK_CACHE['last_check'] < 30):
        return _MYSQL_CHECK_CACHE['available']

    # Fast 0.5s socket check
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    reachable = False
    try:
        s.connect((Config.DB_HOST, Config.DB_PORT))
        reachable = True
        s.close()
    except Exception:
        reachable = False

    _MYSQL_CHECK_CACHE['available'] = reachable
    _MYSQL_CHECK_CACHE['last_check'] = now
    return reachable

def get_connection():
    """
    Establish a connection to MySQL if possible, otherwise SQLite.
    Returns (connection, db_type).
    """
    global ACTIVE_DB_TYPE

    # Try MySQL if configured and reachable
    if Config.DB_TYPE == 'mysql' and is_mysql_reachable():
        try:
            import MySQLdb
            import MySQLdb.cursors

            # First connect to server to ensure DB exists
            try:
                srv_conn = MySQLdb.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    passwd=Config.DB_PASSWORD,
                    connect_timeout=2,
                    charset='utf8mb4'
                )
                srv_cur = srv_conn.cursor()
                srv_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                srv_conn.commit()
                srv_cur.close()
                srv_conn.close()
            except Exception:
                pass

            conn = MySQLdb.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                passwd=Config.DB_PASSWORD,
                db=Config.DB_NAME,
                connect_timeout=2,
                charset='utf8mb4',
                cursorclass=MySQLdb.cursors.DictCursor,
                autocommit=False
            )
            ACTIVE_DB_TYPE = 'mysql'
            return conn, 'mysql'
        except Exception as ex:
            logger.warning("MySQL connection failed (%s). Falling back to persistent SQLite at %s", ex, Config.SQLITE_PATH)
            _MYSQL_CHECK_CACHE['available'] = False

    # SQLite persistent fallback
    conn = sqlite3.connect(Config.SQLITE_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    ACTIVE_DB_TYPE = 'sqlite'
    return conn, 'sqlite'


class Database:
    """Convenient abstraction for executing queries and transactions."""

    @staticmethod
    def _normalize_sql(sql: str, db_type: str) -> str:
        """Convert %s placeholders to ? for SQLite if needed."""
        if db_type == 'sqlite':
            # Replace %s with ?
            return sql.replace('%s', '?')
        return sql

    @classmethod
    def query_all(cls, sql: str, params: tuple = ()) -> list:
        conn, db_type = get_connection()
        try:
            sql_norm = cls._normalize_sql(sql, db_type)
            cursor = conn.cursor()
            cursor.execute(sql_norm, params)
            rows = cursor.fetchall()
            cursor.close()
            if db_type == 'sqlite':
                return [dict(r) for r in rows]
            return list(rows)
        finally:
            conn.close()

    @classmethod
    def query_one(cls, sql: str, params: tuple = ()):
        conn, db_type = get_connection()
        try:
            sql_norm = cls._normalize_sql(sql, db_type)
            cursor = conn.cursor()
            cursor.execute(sql_norm, params)
            row = cursor.fetchone()
            cursor.close()
            if row is None:
                return None
            if db_type == 'sqlite':
                return dict(row)
            return dict(row)
        finally:
            conn.close()

    @classmethod
    def execute(cls, sql: str, params: tuple = (), commit: bool = True):
        conn, db_type = get_connection()
        try:
            sql_norm = cls._normalize_sql(sql, db_type)
            cursor = conn.cursor()
            cursor.execute(sql_norm, params)
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            if commit:
                conn.commit()
            cursor.close()
            return {'lastrowid': last_id, 'rowcount': row_count}
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    @contextmanager
    def transaction(cls):
        """Context manager for running multi-step database transactions."""
        conn, db_type = get_connection()
        cursor = conn.cursor()
        try:
            class TxRunner:
                def __init__(self, c, cur, dt):
                    self.conn = c
                    self.cur = cur
                    self.dt = dt

                def execute(self, sql_stmt, p=()):
                    s = Database._normalize_sql(sql_stmt, self.dt)
                    self.cur.execute(s, p)
                    return self.cur

                def query_one(self, sql_stmt, p=()):
                    s = Database._normalize_sql(sql_stmt, self.dt)
                    self.cur.execute(s, p)
                    r = self.cur.fetchone()
                    if r is None:
                        return None
                    return dict(r)

                def query_all(self, sql_stmt, p=()):
                    s = Database._normalize_sql(sql_stmt, self.dt)
                    self.cur.execute(s, p)
                    res = self.cur.fetchall()
                    if self.dt == 'sqlite':
                        return [dict(x) for x in res]
                    return list(res)

            runner = TxRunner(conn, cursor, db_type)
            yield runner
            conn.commit()
        except Exception as err:
            conn.rollback()
            raise err
        finally:
            cursor.close()
            conn.close()


def init_database():
    """Initialize database tables and schema."""
    conn, db_type = get_connection()
    try:
        cursor = conn.cursor()

        if db_type == 'mysql':
            # Execute MySQL schema
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            # Execute statement by statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt.upper().startswith(('CREATE DATABASE', 'USE')):
                    continue
                try:
                    cursor.execute(stmt)
                except Exception as ex:
                    logger.debug("MySQL init statement ignored: %s", ex)
            conn.commit()
        else:
            # SQLite schema initialization
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT DEFAULT NULL,
                role TEXT DEFAULT 'customer',
                cine_points INTEGER DEFAULT 450,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS movies (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                language TEXT NOT NULL,
                rating REAL DEFAULT 8.0,
                votes TEXT DEFAULT '10K',
                duration TEXT NOT NULL,
                certificate TEXT NOT NULL,
                poster TEXT NOT NULL,
                backdrop TEXT NOT NULL,
                synopsis TEXT,
                cast TEXT,
                director TEXT,
                trailer_url TEXT,
                formats TEXT DEFAULT 'Dolby Atmos 7.1',
                status TEXT DEFAULT 'now_showing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS screens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                features TEXT DEFAULT '4K Laser & Dolby Atmos',
                total_seats INTEGER DEFAULT 80
            );

            CREATE TABLE IF NOT EXISTS seat_definitions (
                id TEXT PRIMARY KEY,
                row_label TEXT NOT NULL,
                seat_number INTEGER NOT NULL,
                tier TEXT NOT NULL,
                price REAL NOT NULL,
                is_vip INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id TEXT NOT NULL,
                screen_id INTEGER NOT NULL,
                show_date TEXT NOT NULL,
                show_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (movie_id) REFERENCES movies(id),
                FOREIGN KEY (screen_id) REFERENCES screens(id),
                UNIQUE(movie_id, screen_id, show_date, show_time)
            );

            CREATE TABLE IF NOT EXISTS seat_holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                show_id INTEGER NOT NULL,
                seat_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_id INTEGER DEFAULT NULL,
                held_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (show_id) REFERENCES shows(id),
                FOREIGN KEY (seat_id) REFERENCES seat_definitions(id),
                UNIQUE(show_id, seat_id)
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_ref TEXT NOT NULL UNIQUE,
                user_id INTEGER DEFAULT NULL,
                show_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT DEFAULT NULL,
                ticket_subtotal REAL NOT NULL,
                snacks_subtotal REAL DEFAULT 0.00,
                convenience_fee REAL DEFAULT 30.00,
                discount_amount REAL DEFAULT 0.00,
                promo_code TEXT DEFAULT NULL,
                total_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'completed',
                payment_method TEXT DEFAULT 'TEST_SANDBOX_GATEWAY',
                payment_ref TEXT DEFAULT NULL,
                qr_token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (show_id) REFERENCES shows(id)
            );

            CREATE TABLE IF NOT EXISTS booked_seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                show_id INTEGER NOT NULL,
                seat_id TEXT NOT NULL,
                price REAL NOT NULL,
                tier TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (show_id) REFERENCES shows(id),
                FOREIGN KEY (seat_id) REFERENCES seat_definitions(id),
                UNIQUE(show_id, seat_id)
            );

            CREATE TABLE IF NOT EXISTS snacks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '🍿',
                price REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS booking_snacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                snack_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (snack_id) REFERENCES snacks(id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                movie_id TEXT NOT NULL,
                user_id INTEGER DEFAULT NULL,
                user_name TEXT NOT NULL,
                email TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (movie_id) REFERENCES movies(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                discount_percent REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS login_page (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                UserName TEXT,
                Email TEXT,
                Password TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS booking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Movie TEXT,
                Seats TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT,
                Email TEXT,
                rate TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

        cursor.close()
    finally:
        conn.close()

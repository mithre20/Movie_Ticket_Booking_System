"""
CineMithresh - Application Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Optional: Load from .env file if available
env_path = BASE_DIR / '.env'
if env_path.exists():
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cinemithresh_dev_secret_key_change_in_production_99440')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    PORT = int(os.environ.get('PORT', 8000))

    # Session cookie security settings
    SESSION_COOKIE_NAME = 'cinemithresh_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True when served over HTTPS in production
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # Database Settings
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql').lower()
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'cinemithresh_db')
    SQLITE_PATH = os.environ.get('SQLITE_DB_PATH', str(BASE_DIR / 'cinemithresh.sqlite3'))

    # Payment Settings
    PAYMENT_MODE = os.environ.get('PAYMENT_MODE', 'test')
    PAYMENT_MERCHANT = os.environ.get('PAYMENT_MERCHANT_NAME', 'CineMithresh Box Office')
    PAYMENT_CURRENCY = os.environ.get('PAYMENT_CURRENCY', 'INR')

    # Seat Hold Configuration
    SEAT_HOLD_TTL_SECONDS = 300  # 5 minutes

    # ==========================================
    # Media / CDN Settings
    # ==========================================
    # All movie posters, backdrops and brand assets are served from external
    # object storage (AWS S3 / CloudFront). No images live in the project
    # directory. Set MEDIA_BASE_URL to your bucket/CDN origin, e.g.
    #   MEDIA_BASE_URL=https://dxxxxxxxx.cloudfront.net
    # When empty, media_url() falls back to a local "./<name>" path so the app
    # keeps working during local development before the bucket is configured.
    MEDIA_BASE_URL = os.environ.get('MEDIA_BASE_URL', '').strip().rstrip('/')

    # CDN-only mode: when True, media_url() refuses to fall back to local
    # "./<name>" paths and raises instead. Enable this once every asset is
    # hosted so a missing MEDIA_BASE_URL fails loudly rather than silently
    # serving stale local files.
    MEDIA_REQUIRE_CDN = os.environ.get('MEDIA_REQUIRE_CDN', 'False').lower() in ('true', '1', 'yes')

    # AWS S3 Settings (used by scripts/upload_media.py)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-south-1')
    S3_BUCKET = os.environ.get('S3_BUCKET', '')
    S3_PREFIX = os.environ.get('S3_PREFIX', '').strip().strip('/')


def media_url(name):
    """Resolve a media filename/key into a full external URL.

    * Absolute http(s)/data URLs are returned unchanged.
    * Values already prefixed with Config.MEDIA_BASE_URL are returned unchanged
      (idempotent, so seeding/migration can be re-run safely).
    * Bare filenames (optionally prefixed with "./") are appended to
      Config.MEDIA_BASE_URL.
    * When MEDIA_BASE_URL is not configured, a local "./<name>" path is
      returned so development still works without a CDN — unless
      MEDIA_REQUIRE_CDN is enabled, in which case a RuntimeError is raised.
    """
    if not name:
        return name
    name = str(name)
    if name.startswith(('http://', 'https://', 'data:')):
        return name

    base = Config.MEDIA_BASE_URL

    # Already resolved (e.g. re-running the migration) — leave untouched.
    if base and (name == base or name.startswith(base + '/')):
        return name
    # Root-relative paths are already servable without a base URL.
    if not base and name.startswith('/'):
        return name

    clean = name.lstrip('./')
    if base:
        return f"{base}/{clean}"
    if Config.MEDIA_REQUIRE_CDN:
        raise RuntimeError(
            "MEDIA_REQUIRE_CDN is enabled but MEDIA_BASE_URL is not set. "
            f"Refusing to fall back to a local media path for {name!r}."
        )
    return f"./{clean}"

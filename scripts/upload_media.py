#!/usr/bin/env python3
"""
CineMithresh - Upload local media (posters, backdrops, brand assets) to AWS S3.

Uploads every image found in the project root to the configured S3 bucket,
keeping the original filename (optionally under S3_PREFIX). Idempotent: safe to
re-run; existing objects are overwritten.

Reads credentials/settings from .env via config.Config:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION,
    S3_BUCKET, S3_PREFIX, MEDIA_BASE_URL

Usage:
    python scripts/upload_media.py
    python scripts/upload_media.py --dry-run
"""

import sys
import mimetypes
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Config  # noqa: E402

MEDIA_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.avif'}

# Images are served from static/media for local development; the project root is
# also scanned for any loose files.
MEDIA_DIRS = [BASE_DIR / 'static' / 'media', BASE_DIR]


def list_media_files():
    """Return all media files from the media folder and the project root."""
    files = {}
    for directory in MEDIA_DIRS:
        if not directory.is_dir():
            continue
        for p in directory.iterdir():
            if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS:
                files.setdefault(p.name, p)
    return [files[name] for name in sorted(files)]


def build_client():
    try:
        import boto3
    except ImportError:
        raise SystemExit("[!] boto3 is not installed. Run: pip install boto3")

    if not Config.S3_BUCKET:
        raise SystemExit("[!] S3_BUCKET is not set. Configure it in .env first.")

    kwargs = {'region_name': Config.AWS_DEFAULT_REGION}
    # Explicit keys are optional; boto3 falls back to its own credential chain.
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        kwargs['aws_access_key_id'] = Config.AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = Config.AWS_SECRET_ACCESS_KEY
    return boto3.client('s3', **kwargs)


def main():
    dry_run = '--dry-run' in sys.argv
    files = list_media_files()
    if not files:
        print(f"[!] No media files found in {BASE_DIR}")
        return

    prefix = f"{Config.S3_PREFIX}/" if Config.S3_PREFIX else ''
    base = Config.MEDIA_BASE_URL.rstrip('/') if Config.MEDIA_BASE_URL else ''

    print(f"[*] {len(files)} media file(s) -> s3://{Config.S3_BUCKET}/{prefix}")
    client = None if dry_run else build_client()

    uploaded = 0
    for path in files:
        key = f"{prefix}{path.name}"
        content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        status = "dry-run"
        if not dry_run:
            with open(path, 'rb') as fh:
                client.put_object(
                    Bucket=Config.S3_BUCKET,
                    Key=key,
                    Body=fh,
                    ContentType=content_type,
                    CacheControl='public, max-age=31536000, immutable',
                )
            uploaded += 1
            status = "ok"
        line = f"  [{status}] {key} ({content_type})"
        if base:
            line += f"\n         -> {base}/{key}"
        print(line)

    if not base:
        print("\n[i] Set MEDIA_BASE_URL in .env to the public origin that serves "
              "these keys (S3 URL or CloudFront domain).")
    print(f"\n[+] Done. {'Would upload' if dry_run else 'Uploaded'} {uploaded if not dry_run else len(files)} file(s).")


if __name__ == '__main__':
    main()

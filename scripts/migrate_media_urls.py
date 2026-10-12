#!/usr/bin/env python3
"""
CineMithresh - Migrate stored movie image paths to external CDN URLs.

The `movies` table stores `poster` and `backdrop`. Older seeds used local paths
like './pushpa_2.jpg'. This script rewrites them to full external URLs built
from MEDIA_BASE_URL in config (see config.media_url). Safe to re-run: rows that
already point at external URLs are left untouched.

Usage:
    python scripts/migrate_media_urls.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Config, media_url  # noqa: E402
from database import Database, init_database  # noqa: E402


def main():
    init_database()

    if not Config.MEDIA_BASE_URL:
        print("[!] MEDIA_BASE_URL is empty. Set it in .env before migrating.")
        print("    Nothing changed (local './<file>' paths are only valid when "
              "MEDIA_BASE_URL is set).")
        return

    movies = Database.query_all("SELECT id, poster, backdrop FROM movies")
    if not movies:
        print("[i] No movies found in the database. Nothing to migrate.")
        return

    updated = 0
    for m in movies:
        new_poster = media_url(m['poster'])
        new_backdrop = media_url(m['backdrop'])
        if new_poster != m['poster'] or new_backdrop != m['backdrop']:
            Database.execute(
                "UPDATE movies SET poster = %s, backdrop = %s WHERE id = %s",
                (new_poster, new_backdrop, m['id']),
            )
            updated += 1
            print(f"  [ok] {m['id']}\n       poster   -> {new_poster}\n       backdrop -> {new_backdrop}")

    print(f"\n[+] Migration complete. Updated {updated} of {len(movies)} movie(s).")


if __name__ == '__main__':
    main()

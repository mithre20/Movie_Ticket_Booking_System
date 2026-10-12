# Media Setup — Hosting Images on AWS S3

CineMithresh serves every poster, backdrop and brand asset from external object
storage. **No images are stored in the project directory or committed to the
repo.** This folder holds the helper scripts that upload local media once and
point the database at the resulting URLs.

## How it works

| Piece | Location | Role |
|---|---|---|
| `MEDIA_BASE_URL` | `.env` (`config.py`) | Backend base URL for building media links (seed + migration). |
| `MEDIA_BASE_URL` | `static/app.js` | Frontend base URL (JS can't read `.env`, so set it here too). |
| `media_url()` | `config.py` | Turns `pushpa_2.jpg` → `<base>/pushpa_2.jpg`. |
| `mediaUrl()` | `static/app.js` | Same, for the browser. |
| `upload_media.py` | this folder | Uploads images from `static/media/` (and the root) to S3. |
| `migrate_media_urls.py` | this folder | Rewrites existing DB rows to the new URLs. |

## Local development (no CDN)

Images live in `static/media/` and are served by Flask at `/static/media/...`.
Set the base URL to that path in both places:

```ini
# .env
MEDIA_BASE_URL=/static/media
```
```js
// static/app.js
const MEDIA_BASE_URL = '/static/media';
```

This is the current default. It needs no AWS account and keeps the project root
(`.env`, the SQLite DB, Python sources) protected. When you later move to S3,
just change this value to the CDN origin.

Both resolvers also accept a bare empty value, which falls back to old
`./<file>` paths — but with the hardened `static_folder='static'`, root files
are **not** served, so prefer `/static/media`.

## One-time setup sequence

### 1. Provision AWS

1. Create an S3 bucket (e.g. `cinemithresh-media`) in `ap-south-1` (Mumbai).
2. Keep **Block Public Access ON** and front the bucket with **CloudFront**
   (Origin Access Control). *Simpler but less secure alternative:* public bucket
   policy + the raw `https://<bucket>.s3.<region>.amazonaws.com` URL.
3. Create an IAM user with only `s3:PutObject` on that bucket.

### 2. Configure `.env`

```ini
MEDIA_BASE_URL=https://dxxxxxxxx.cloudfront.net
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=cinemithresh-media
# optional key prefix inside the bucket
S3_PREFIX=
# CDN-only mode (see below) — keep False until upload+verify succeed
MEDIA_REQUIRE_CDN=False
```

### 3. Preview and upload

```bash
python scripts/upload_media.py --dry-run   # list files + resulting URLs
python scripts/upload_media.py             # actually upload
```

Objects get `CacheControl: public, max-age=31536000, immutable` and the correct
`Content-Type`. The script is idempotent — re-running overwrites existing keys.

### 4. Migrate existing database rows

Old seeds stored `./pushpa_2.jpg`. This rewrites them in place (safe to re-run):

```bash
python scripts/migrate_media_urls.py
```

### 5. Point the frontend at the CDN

Edit `static/app.js` and set the same origin:

```js
const MEDIA_BASE_URL = 'https://dxxxxxxxx.cloudfront.net';
```

### 6. Verify, then clean up

```
/
/booking.html
/ratings.html
/about_us.html
/login.html
```

Confirm every image loads from the configured origin (check the browser
Network tab). For a full CDN migration, **only after that** you may delete the
files in `static/media/` — until the CDN is verified they are the local copy.

## CDN-only mode

Once all assets are hosted and verified, lock the project into CDN-only mode:

```ini
# .env
MEDIA_REQUIRE_CDN=True
```

```js
// static/app.js
const MEDIA_REQUIRE_CDN = true;
```

Behaviour when enabled and `MEDIA_BASE_URL` is missing:

- **Backend** (`config.media_url`) raises `RuntimeError` — seeding/migration
  fails fast instead of writing broken local paths.
- **Frontend** (`mediaUrl`) logs an error and renders the "No Image"
  placeholder instead of a broken local path.

## Notes

- Missing/expired external URLs degrade gracefully: every `<img>` uses
  `onerror="mediaFallback(this)"`, which swaps in an inline SVG placeholder.
- `upload_media.py` uploads **all** images found in `static/media/` (and the
  project root), including a few currently unused ones (`logo.jpg`,
  `background.jpg`, `movie.jpg`, `movie3.jpg`, `background1/3/4/5/6.png`).
  Harmless, but you can delete the unused ones instead of uploading them.
- Legacy routes `/connection1.py`, `/register.py`, `/rating.py` still serve
  those `.py` stubs and are unrelated to media handling.

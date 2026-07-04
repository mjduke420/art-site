# Photo Portfolio + Blog

A self-hosted, Flickr-style photo portfolio with a blog and a hidden admin area
for uploading albums, photos, and posts. Built as a single Docker container
(FastAPI + SQLite + Jinja templates) designed to run as a Portainer stack.

## Features

- **Album grid** home page → **masonry album** view with a keyboard-navigable lightbox
- **Blog** with Markdown posts, cover images, and draft/published states
- **Hidden admin** at `/admin` (no public link): album & photo CRUD, drag-and-drop
  multi-upload with automatic thumbnails, drag-to-reorder, blog editor, site settings,
  and an in-app **change password** form
- **Dark mode** throughout, on both the public site and the admin area
- **Single container, single volume** — SQLite database and uploaded images both live
  under `/data`, so everything survives redeploys
- Security: bcrypt-hashed admin password (changeable from the admin UI), CSRF-protected
  forms, upload validation, all secrets from environment variables

## Tech stack

FastAPI · SQLAlchemy 2 · SQLite · Jinja2 · Pillow · Uvicorn

## Project layout

```
app/
  main.py            # app wiring: middleware, mounts, startup seeding
  config.py          # env-driven settings
  database.py        # engine + session
  models/            # Album, Photo, BlogPost, User, Setting
  security.py        # password hashing, CSRF, admin auth
  services/          # storage, image processing, markdown, settings, seeding
  routers/           # public, blog, admin_*
  templates/         # Jinja2 (public/ + admin/)
  static/            # css + js
images/              # empty by default; not used for auto-seeding
tests/               # pytest suite
Dockerfile · docker-compose.yml
```

## Configuration

Copy `.env.example` to `.env` and set values (or set them in Portainer's stack env):

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **yes** | Signs the session cookie. Use a long random string. |
| `ADMIN_PASSWORD` | **yes** | Admin login password (hashed into the DB on first run). Change it from `/admin/settings` afterward. |
| `ADMIN_USERNAME` | no | Defaults to `admin`. |
| `SITE_TITLE` | no | Public site title (also editable in admin settings). |
| `MAX_UPLOAD_MB` | no | Per-image upload limit. Defaults to `25`. |
| `DATA_DIR` | no | Where the DB + uploads live. `/data` in Docker. |

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> The app logs a security warning at startup if `SECRET_KEY`/`ADMIN_PASSWORD`
> are left at their defaults. Change them before exposing the site — or just log
> in once and use **Admin → Settings → Change password**.

## Run with Docker

```bash
cp .env.example .env        # then edit SECRET_KEY and ADMIN_PASSWORD
docker compose up -d --build
```

Visit http://localhost:8090 — admin at http://localhost:8090/admin.

### Deploy on Portainer

The stack **builds the image on the host** from this repo — no container registry
required.

1. **Stacks → Add stack → Repository**, point it at this repo and supply your access
   token (the repo is private). Portainer clones it and builds the image.
2. Add stack environment variables: `SECRET_KEY`, `ADMIN_PASSWORD` (and optionally
   `ADMIN_USERNAME`, `SITE_TITLE`, `MAX_UPLOAD_MB`).
3. Deploy. The named volume `portfolio_data` holds the database and all uploads —
   keep it across updates and back it up to preserve your content.

To update later: redeploy the stack so Portainer re-pulls the repo and rebuilds.
Leave any **"re-pull image"** option **off** — `pull_policy: build` in the compose
keeps Portainer building from source instead of looking for a registry image.

On first start the app creates the database, the admin user, and default site
settings (title, tagline, about text, contact email) — all editable from
`/admin/settings`. There are no starter albums; create your first album from
the admin UI.

## Local development

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

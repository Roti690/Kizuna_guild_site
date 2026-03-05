# Kizuna Guild Site

FastAPI-powered guild website for the **Kizuna** community (Where Winds Meet), with public pages and an officer/admin panel for managing members, events, and guides.

## Features

- Public pages: Home, Members, Events, Builds/Guides, and Rules (`/szabalyzat`)
- Guild member roster with activity tracking statuses
- Officer panel for member management, weekly status roll-over, and event schedule updates
- Markdown-based guide system with image uploads and public guide pages
- Local posts + scraped official Where Winds Meet news on the homepage
- SQLite by default, configurable via `DATABASE_URL`

## Tech Stack

- Python 3.12
- FastAPI + Starlette sessions
- Jinja2 templates + static CSS assets
- SQLAlchemy ORM
- SQLite (default)
- Uvicorn

## Quick Start (Local)

```bash
git clone https://github.com/Roti690/Kizuna_guild_site.git
cd Kizuna_guild_site
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set secure values in `.env`:

```env
SESSION_SECRET=replace-with-a-long-random-secret
OFFICER_PASSWORD=replace-with-a-strong-password
# DATABASE_URL=sqlite:///./kizuna.db
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/`
- Officer login: `http://127.0.0.1:8000/officer/login`

## Environment Variables

- `SESSION_SECRET`: session signing key for officer auth
- `OFFICER_PASSWORD`: password used on `/officer/login`
- `DATABASE_URL`: SQLAlchemy database URL (defaults to `sqlite:///./kizuna.db`)
- `PORT`: server port in container/deployment environments

## Main Routes

### Public

- `GET /` - homepage with guild info + news
- `GET /members` - roster grouped by role
- `GET /events` - weekly event schedule
- `GET /builds` - guide listing
- `GET /builds/{slug}` - guide detail page (Markdown rendered)
- `GET /szabalyzat` - rules page

### Officer / Admin

- `GET /officer/login` - login form
- `POST /officer/login` - authenticate officer session
- `GET /_officer` - admin dashboard
- `POST /_officer/add` - add member
- `POST /_officer/update/{member_id}` - update member
- `POST /_officer/delete/{member_id}` - delete member
- `POST /_officer/roll-week` - roll activity week data
- `POST /_officer/events/update` - update event times
- `GET /_officer/guides` - manage guides
- `POST /_officer/guides/create` - create guide
- `POST /_officer/guides/update/{guide_id}` - update guide
- `POST /_officer/guides/delete/{guide_id}` - delete guide

### JSON API (`/api`)

- `GET /api/members`
- `POST /api/members`
- `PATCH /api/members/{member_id}`
- `POST /api/members/roll-week`
- `GET /api/posts`
- `POST /api/posts`

## Docker

Build and run:

```bash
docker build -t kizuna-guild-site .
docker run --rm -p 8080:8080 \
  -e SESSION_SECRET='replace-me' \
  -e OFFICER_PASSWORD='replace-me' \
  kizuna-guild-site
```

The container starts with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## Fly.io Notes

Repository includes `fly.toml` configured for:

- app name: `kizuna-guild-site`
- internal port: `8080`
- persistent volume mount at `/data`
- `DATABASE_URL=sqlite:////data/kizuna.db`

## Project Structure

```text
app/
  main.py             # FastAPI app factory + router mounting
  config.py           # Settings from environment/.env
  db.py               # Engine/session setup + migration helper
  models.py           # SQLAlchemy models
  routes/             # Public, API, auth, and officer routes
  services/wwm_news.py# Where Winds Meet news scraping/cache
  templates/          # Jinja2 HTML templates
  static/             # CSS, images, and uploaded assets
```

## Security / Ops Notes

- Change default secrets before deployment.
- `https_only` in session middleware is currently `False`; set to `True` behind HTTPS.
- Uploaded guide images are stored in `app/static/uploads`.

## License

No license file is currently included in this repository.

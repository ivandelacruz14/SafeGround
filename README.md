# SafeRoute

Public transport route planning and flood awareness for Metro Manila, built to expand nationwide.
This repository currently contains **Phase 1**: foundation, authentication, roles, database and the map interface.
See `docs/PLAN.md` for the full plan, schema, API outline, data-source investigation and milestones.

## Status

| Area | Phase 1 |
|---|---|
| Auth: register, email verification, login, refresh cookie, roles (user / moderator / admin), profile | Done |
| Preferences and saved places | Done |
| MySQL 8 schema with spatial indexes, Alembic migration, seed script | Done |
| Live map with place search, map-click pins, optional "use my location", layer panel, stop markers | Done |
| Admin: users, data sources, audit logs | Done |
| OpenAPI docs at `/api/v1/docs` | Done |
| Transport data, fares, journey planner, flood, reports, AI, notifications | Not built. Pages say so and show no invented data |

**Not yet verified by running.** The code was written in an environment without MySQL or package installs, so tests and the
app have been syntax-checked only. Run the steps below and the test commands before trusting anything. Items most likely
to need a fix are listed under "First-run checklist".

## Requirements

Python 3.11+, Node 20+, Docker (for MySQL 8.4) or your own MySQL 8.

## Setup

```bash
cp .env.example .env            # then edit: set SECRET_KEY, JWT_SECRET_KEY, passwords
python -c "import secrets; print(secrets.token_urlsafe(48))"   # run twice for the two keys

docker compose up -d db         # wait until healthy: docker compose ps

cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
export FLASK_APP=wsgi.py        # Windows PowerShell: $env:FLASK_APP="wsgi.py"
flask db upgrade                # creates all Phase 1 tables
SEED_ADMIN_EMAIL=you@example.com SEED_ADMIN_PASSWORD='a-long-password-12+' flask seed
flask seed-demo                 # optional: 3 fictional stops labeled DEMO
flask run --port 5000

# second terminal
cd frontend
npm install
npm run dev                     # http://localhost:5173 (proxies /api to port 5000)
```

With `MAIL_BACKEND=console`, the verification link is printed in the Flask terminal. API docs: http://localhost:5000/api/v1/docs

## Tests

```bash
cd backend && pytest                       # SQLite, no MySQL needed
TEST_MYSQL_URL='mysql+pymysql://root:PASSWORD@127.0.0.1:3306/saferoute_test' pytest tests/test_mysql_spatial.py
cd frontend && npm test
```

The MySQL spatial test is the one that proves `POINT SRID 4326`, `ST_GeomFromText` axis order and `MBRContains` behave as the
code assumes. Create an empty `saferoute_test` database first. Run it before anything else.

## First-run checklist

1. `flask db upgrade` succeeds on MySQL 8 and `SHOW INDEX FROM route_stops` lists a SPATIAL index on `location`.
2. `tests/test_mysql_spatial.py` passes. If `MBRContains` misbehaves on SRID 4326, switch the bbox query in
   `blueprints/transport.py` to `ST_Contains` on an `ST_Envelope`.
3. `pytest` passes. Cookie and CSRF behavior (`test_refresh_requires_csrf_header`) depends on your Flask-JWT-Extended version.
4. Register, verify via the logged link, sign in, reload the page (session should restore through the refresh cookie).
5. Open the live map: the layer panel should say no stop data has been imported, or show demo stops if you seeded them.

## Data honesty rules built in

* Stops, routes and sources carry `verification_status` and a `data_sources` row. Demo data is labeled DEMO and never shown as verified.
* The layer endpoint reports `available`, `no_data` or `planned`. The UI never treats missing data as safe.
* `data_sources.access_status` starts as `unverified` for GTFS, PAGASA, FloodCaster, MMDA and DOTr. No integration is assumed to exist.

## Privacy

* Device location is requested only after you press "Use my location", is used in the browser, and is never sent to the server.
  Saving a place stores only the coordinates you choose to save, visible only to your account.
* Place search sends your query text to the configured geocoder (public Nominatim by default). Self-host it for production.

## Map tiles

`tile.openstreetmap.org` is for development only (OSM tile usage policy). For production set `VITE_TILE_URL` and
`VITE_TILE_ATTRIBUTION` to a commercial provider or your own tile server, and keep attribution visible.

## Deployment outline

* Build the frontend (`npm run build`) and serve `frontend/dist` from a static host or Nginx. Route `/api` to Gunicorn on the same origin
  (keeps the refresh cookie first-party). If origins differ, set `CORS_ORIGINS`, `JWT_COOKIE_SAMESITE=None` and HTTPS.
* Backend: `APP_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app`, behind TLS, with `TRUST_PROXY=true` when behind a proxy.
  Production refuses to start with missing or weak secrets.
* Use a shared rate-limit store (`RATELIMIT_STORAGE_URI=redis://...`) with multiple workers.
* Run `flask db upgrade` on each release. Back up MySQL. Set `MAIL_BACKEND=smtp`.

## Known limits in Phase 1

* No refresh-token revocation list (logout clears the cookie; suspension takes effect on the next request).
* Geocode cache is per process.
* Place search is submit-only (no autocomplete) to respect the Nominatim usage policy.
* The password reset flow is not built yet.

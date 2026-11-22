# SafeRoute implementation plan

## Folder structure
```
backend/   Flask app (app/blueprints per module), models, Alembic migrations, tests, OpenAPI spec
frontend/  React + Vite + Tailwind + Framer Motion + Leaflet
docs/      this plan; docker-compose.yml and .env.example live at the repo root
```
Later phases add: `backend/app/importers/` (GTFS, OSM, manual CSV adapters), `backend/app/services/routing.py`
(OpenTripPlanner client), `services/flood.py`, `services/ai.py`, and `docker-compose` services for OpenTripPlanner and Redis.

## Schema
Implemented in migration 0001: roles, users, user_preferences, saved_places, data_sources, transport_modes,
transport_operators, transport_routes, route_stops, route_stop_sequences, audit_logs.

Planned, in the phase that needs each:
* Phase 2: route_shapes, route_schedules, fare_matrices (versioned: valid_from / valid_to, never updated in place), transit_connections, data_import_logs
* Phase 3: journeys, journey_legs
* Phase 4: flood_zones, flood_reports, flood_observations, road_reports, report_evidence, report_verifications
  (each report: source_type, status, confidence, reported_at, verified_at, expires_at; four separate trust classes)
* Phase 5: notifications, ai_conversations, ai_recommendations

Conventions: InnoDB, utf8mb4, FKs, indexes on lookup columns, `POINT SRID 4326` with SPATIAL indexes (NOT NULL),
created_at/updated_at, status columns, no hard deletes of historical records.

## API (all under /api/v1)
Phase 1 is documented in `backend/app/openapi.yaml`. Planned prefixes: `/transport/*` (routes, stops, fares, nearby),
`/journeys/*` (plan, save), `/flood/*`, `/reports/*` (submit, evidence upload, moderation), `/ai/*` (chat; tool-calling over backend data only),
`/notifications/*`, `/admin/*` (transport, fares, imports, sources, analytics). WebSockets (Flask-SocketIO) for report and alert pushes in Phase 4-5.

## External data: what must be verified before use
| Source | Need | Status |
|---|---|---|
| OpenStreetMap | Base map, geocoding, walking network | Usable under ODbL with attribution. Public tile and Nominatim servers are rate-limited and not for production load |
| GTFS for Metro Manila | Stops, routes, schedules for OpenTripPlanner | **Unverified.** Locate feeds, check licence, freshness and completeness. Fallback: admin CSV import and manual entry |
| PAGASA | Official rainfall and flood advisories | **Unverified.** Confirm whether a data API exists, terms of reuse and update cadence |
| FloodCaster | Flood forecasts | **Unverified.** Confirm access and licensing |
| MMDA | Traffic, closures | **Unverified.** No public API assumed |
| LTFRB / DOTr | Franchised routes, fare issuances, rail data | **Unverified.** Fares entered by admins from official issuances with a citation and effective date |

Rule: a source is not used until its `data_sources.access_status` is set to `verified_access` by an admin after checking these points.
Stale or manual data is displayed with its timestamp and never labeled live.

## Milestones
1. **Phase 1 (this delivery):** foundation, auth, roles, schema, map shell, dark UI.
2. **Phase 2:** importers, route and stop management, versioned fares, route lines on map.
3. **Phase 3:** OpenTripPlanner (GTFS + OSM) client, journey planner with fastest / cheapest / fewest-transfer / flood-aware.
4. **Phase 4:** flood layers by trust class, community reports, moderation, duplicate detection, expiry jobs, uploads.
5. **Phase 5:** AI assistant (LLM calls backend tools, answers only from returned data with sources), notifications.
6. **Phase 6:** admin completion, analytics, security review, load tests, deployment pipeline.
7. **Phase 7:** region model for nationwide expansion (region-scoped imports, tile and OTP graph per region).

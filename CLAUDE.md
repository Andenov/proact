# PROACT — Claude Code Project Brief

## What this is
AI-powered anticipatory action platform for climate risk, food security, and farmer alerting.
Piloting in Northern and Eastern Uganda: Mbale, Bududa, Sironko, Moroto, Kotido.

## Stack
- **Frontend**: Next.js 16 (Turbopack), TypeScript, Tailwind, Leaflet, Recharts, TanStack Query
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, GeoAlchemy2, APScheduler
- **Database**: PostgreSQL + PostGIS
- **Weather**: Open-Meteo API (free, no key) — 16-day forecast + archive
- **Soil moisture**: NASA POWER (free, no key)
- **SMS**: Mock provider by default; Africa's Talking via `SMS_PROVIDER=africas_talking`

## Running locally
```
docker-compose up --build        # first time
docker-compose up                # subsequent runs
```
- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Default admin: admin@proact.org / proact2024

## Key architecture
- `apps/api/app/services/risk_engine.py` — scoring logic (flood, landslide, food stress)
- `apps/api/app/core/weights.json` — calibrated ML weights (if present, overrides defaults)
- `apps/api/app/core/weights.py` — weight loader (falls back to defaults if no JSON)
- `apps/api/app/services/forecast_service.py` — 4-horizon risk outlook (today/7d/14d/30d)
- `apps/api/app/services/calibration.py` — logistic regression weight calibration
- `apps/api/scripts/calibrate_weights.py` — run calibration from inside the API container
- `apps/api/jobs/tasks.py` — daily pipeline: ingest → compute risk → generate alerts
- `apps/web/src/components/dashboard/DistrictAlertPanel.tsx` — right panel with risk + forecast timeline

## ML calibration
Weights are calibrated from historical Uganda disaster events in `data/events/historical_events.csv`.
To re-calibrate:
```
docker-compose run --rm api python scripts/calibrate_weights.py
docker-compose restart api
```

## Seed data after fresh start
```
POST /ingest/weather       # fetch Open-Meteo + NASA POWER data
POST /ingest/compute-risk  # compute risk scores for all districts
POST /alerts/generate      # generate alerts from scores
```

## Conventions
- Python: no type comments, use type hints in function signatures
- TypeScript: strict, no `any` unless unavoidable
- No mock data in production code paths
- Weights in risk_engine.py are loaded dynamically — never hardcode them directly

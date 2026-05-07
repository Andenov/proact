# PROACT — Anticipatory Action Platform

An AI-powered climate risk and farmer alerting system for Uganda.

## What It Does

- Monitors 5 pilot districts in Northern and Eastern Uganda
- Computes daily flood, landslide, and food stress risk scores using Open-Meteo weather data
- Displays district-level risk on an interactive dashboard with map, alerts, and trend charts
- Sends SMS alerts to enrolled smallholder farmers (mock provider by default)

## Quick Start

### Prerequisites
- Docker + Docker Compose
- OR: Python 3.11+, Node 20+, PostgreSQL 15 with PostGIS

### Option A — Docker (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

Then visit:
- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs

### Option B — Local development

**1. Database**
```bash
# Start PostgreSQL with PostGIS locally, then:
createdb proact
```

**2. Backend**
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env
# Edit .env with your DATABASE_URL
uvicorn app.main:app --reload --port 8000
```

On first start, the API automatically:
- Creates all tables
- Seeds 5 pilot districts and hazard features
- Seeds 12 sample farmers
- Creates admin user: `admin@proact.org` / `proact2024`

**3. Frontend**
```bash
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Visit http://localhost:3000

## Running the Data Pipeline

After starting the API, trigger data ingestion:

```bash
# Fetch weather data from Open-Meteo (last 37 days + 7-day forecast)
curl -X POST http://localhost:8000/ingest/weather

# Compute risk scores for all districts
curl -X POST http://localhost:8000/ingest/compute-risk

# Generate alerts from risk scores
curl -X POST http://localhost:8000/alerts/generate
```

The scheduler also runs this pipeline automatically at 06:00 UTC daily.

## Project Structure

```
proact/
  apps/
    api/          FastAPI backend (Python 3.11)
    web/          Next.js 14 frontend (TypeScript + Tailwind)
  data/
    seed/         District, farmer, and hazard seed data
  infra/
    docker/       Dockerfiles
  docker-compose.yml
  .env.example
```

## API Reference

Full OpenAPI docs at http://localhost:8000/docs

Key endpoints:
- `GET /districts` — List districts with latest risk
- `GET /risk/latest` — Latest risk scores (filterable by type/district)
- `GET /risk/history?district_id=1` — 30-day risk history
- `GET /alerts` — All alerts (filterable)
- `POST /alerts/generate` — Generate alerts from current scores
- `POST /sms/send` — Send SMS to a district's farmers
- `GET /sms/logs` — SMS delivery log
- `POST /ingest/weather` — Fetch weather from Open-Meteo
- `POST /ingest/compute-risk` — Recompute all risk scores

## SMS Configuration

Default is mock mode (no real SMS sent, logs to console + DB).

To use Africa's Talking:
```
SMS_PROVIDER=africas_talking
AT_USERNAME=your_username
AT_API_KEY=your_api_key
```

## Default Admin Credentials

- Email: `admin@proact.org`
- Password: `proact2024`

**Change before deploying to production.**

## Pilot Districts

| District | Region | Primary Hazards |
|----------|--------|-----------------|
| Mbale | Eastern | Flood, Landslide |
| Bududa | Eastern | Landslide (high baseline) |
| Sironko | Eastern | Flood, Food Stress |
| Moroto | Karamoja | Drought / Food Stress |
| Kotido | Karamoja | Drought / Food Stress |

## Risk Score Logic

Simple, explainable rule-based scoring (0–100):

- **Flood**: Weighted sum of 3-day rainfall, 7-day rainfall, anomaly score, floodplain exposure
- **Landslide**: Weighted sum of 3-day rainfall, 7-day rainfall, slope index, baseline score
- **Food Stress**: Weighted sum of 30-day deficit, heat stress days × seasonal multiplier

Levels: Low (<40) / Medium (40–69) / High (≥70) [flood]; similar thresholds for others.

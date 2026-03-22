# MedNews

MedNews is a medical news aggregator that monitors 100+ Hungarian and international medical/pharmaceutical news sources (RSS feeds, Twitter/X accounts), enriches each article with LLM-powered scoring and Hungarian-language satirical summaries, and serves them through a FastAPI backend and a Vue 3 SPA frontend with infinite scroll, full-text search, date/region filters, and social sharing.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Earlier versions not tested |
| Node.js | 20+ | For the Vue frontend |
| LLM API key | — | OpenAI-compatible endpoint (Azure AI Foundry, OpenAI, etc.) |
| Twitter Bearer Token | — | Optional — for Twitter/X source monitoring (Basic tier, $100/mo) |

---

## Quick Start (Development)

### 1. Clone the repository

```bash
git clone https://github.com/yourorg/mednews.git
cd mednews
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://your-endpoint.openai.azure.com/v1
ADMIN_API_KEY=some_strong_random_string
VITE_ADMIN_API_KEY=some_strong_random_string
```

See the [Environment Variables](#environment-variables) table for all options.

### 3. Create and activate the Python virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the database

Run Alembic migrations (recommended):
```bash
alembic upgrade head
```

Or use the database module directly:
```bash
python -m backend.database
```

### 6. Seed news sources

```bash
python -m backend.seeds.sources
```

This seeds 100+ sources (Hungarian medical portals, RSS feeds, Twitter/X accounts, EU/US health IT feeds).

### 7. Start the backend

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 8. Start the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

The Vue SPA will be available at `http://localhost:5173`.

---

## Production Deployment

The `deploy/setup.sh` script bootstraps a clean Ubuntu 24 LTS server end-to-end.

### Steps

1. Copy the project to the server:
   ```bash
   rsync -av --exclude='.venv' --exclude='node_modules' --exclude='*.db' \
       ./ user@yourserver:/opt/mednews/
   ```

2. SSH into the server and run the bootstrap script:
   ```bash
   ssh user@yourserver
   sudo bash /opt/mednews/deploy/setup.sh
   ```

   The script will pause and ask you to edit `/opt/mednews/.env` before continuing. Set `LLM_API_KEY`, `LLM_BASE_URL`, and `ADMIN_API_KEY` at minimum.

3. After setup completes, update the nginx `server_name` directive:
   ```bash
   sudo nano /etc/nginx/sites-available/mednews
   # Change: server_name _;
   # To:     server_name yourdomain.com;
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. Obtain a TLS certificate with Certbot:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

What `setup.sh` does automatically:
- Installs Python 3.11, Node 20, nginx
- Creates a `mednews` system user
- Sets up the Python virtual environment and installs dependencies
- Runs `alembic upgrade head`
- Seeds 100+ news sources
- Builds the Vue frontend (`npm run build`)
- Installs and enables the `mednews` systemd service
- Configures nginx as a reverse proxy

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | Yes | — | API key for OpenAI-compatible LLM endpoint |
| `LLM_BASE_URL` | Yes | — | Base URL for LLM API (e.g. Azure AI Foundry endpoint) |
| `LLM_MODEL` | No | `gpt-5.4-mini` | Model name for scoring and enrichment |
| `ADMIN_API_KEY` | Yes | `change_me...` | Secret key for `X-Admin-Key` header on admin endpoints |
| `TWITTER_BEARER_TOKEN` | No | — | Twitter/X API Bearer token for monitoring X accounts |
| `RELEVANCE_THRESHOLD` | No | `6` | Minimum relevance score (1–10) to save an article |
| `DB_PATH` | No | `./mednews.db` | Path to the SQLite database file |
| `HOST` | No | `0.0.0.0` | Backend bind host |
| `PORT` | No | `8000` | Backend bind port |
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Backend URL used by Vite at build time |
| `VITE_ADMIN_API_KEY` | No | `change_me...` | Admin key used by the frontend admin panel |

---

## Running Tests

### Backend (pytest)

```bash
# All tests
pytest tests/ -v

# Smoke test only
pytest tests/test_smoke.py -v

# API tests only
pytest tests/test_api/ -v
```

### Frontend (Vitest)

```bash
cd frontend
npm test -- --run
```

Or using Make:
```bash
make frontend-test
```

---

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make install` | Install all backend and frontend dependencies |
| `make install-backend` | Create venv and install Python dependencies |
| `make install-frontend` | Run `npm install` in the frontend directory |
| `make dev-backend` | Start uvicorn with `--reload` |
| `make dev-frontend` | Start Vite dev server |
| `make test` | Run all pytest tests |
| `make test-smoke` | Run smoke tests only |
| `make test-api` | Run API tests only |
| `make frontend-test` | Run Vitest suite (non-interactive) |
| `make build-frontend` | Build Vue SPA for production |
| `make migrate` | Run `alembic upgrade head` |
| `make migrate-new msg="..."` | Create a new Alembic revision |
| `make seed` | Seed news sources into the database |
| `make lint` | Run `ruff check backend/` |
| `make deploy` | Copy project to `/opt/mednews` and run `setup.sh` (Linux only) |

---

## Architecture Overview

```
mednews/
├── backend/
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Pydantic settings (env vars)
│   ├── database.py        # SQLAlchemy engine + FTS5 triggers
│   ├── models/            # ORM models (Article, Source, AuditLog)
│   ├── api/               # Route handlers (/articles, /search, /admin, /health)
│   ├── scraper/
│   │   └── runner.py      # Async RSS + Twitter/X fetcher
│   ├── services/
│   │   ├── scorer.py      # LLM relevance scoring (1–10)
│   │   ├── enrichment.py  # LLM Hungarian title/summary generation
│   │   └── scheduler.py   # APScheduler (daily scrape 05:00 CET)
│   ├── schemas/           # Pydantic response schemas
│   └── seeds/             # Source seed data (100+ sources)
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue components (ArticleCard, AppHeader, ...)
│   │   ├── composables/   # useSearch, useInfiniteScroll
│   │   ├── views/         # Home, Article, Admin views
│   │   └── stores/        # Pinia store (articles, region filter)
│   └── dist/              # Production build (served by nginx)
├── deploy/
│   ├── setup.sh           # Ubuntu 24 LTS bootstrap script
│   ├── mednews.service    # systemd unit file
│   └── nginx.conf         # nginx reverse proxy config
├── tests/                 # pytest test suite
├── alembic/               # Database migrations
├── .env.example           # Environment variable template
└── Makefile               # Developer shortcuts
```

### Data Pipeline

```
RSS Feeds ─┐
            ├──▶ Async Runner ──▶ LLM Scorer ──▶ LLM Enricher ──▶ SQLite + FTS5
Twitter/X ─┘      (feedparser)    (relevance     (HU title,       (deduped by URL)
                   (httpx v2 API)  score 1–10)    bullet summary,
                                                  tragic detection)
```

### Source Distribution (102 sources)

| Type | Count | Region | Count |
|------|-------|--------|-------|
| RSS feeds | 41 | HU | 54 |
| Portals | 23 | US | 31 |
| Twitter/X | 20 | EU | 17 |
| International | 15 | | |
| Social | 3 | | |

For full requirements and acceptance criteria, see [PRD.md](PRD.md).

---

## Admin Panel

The admin panel is accessible at `/admin` in the frontend.

- **Backend admin endpoints** require the `X-Admin-Key` header set to the value of `ADMIN_API_KEY` in your `.env`.
- **Frontend admin panel** reads `VITE_ADMIN_API_KEY` from the frontend environment at build time.

Admin capabilities include triggering manual scrape runs, viewing scheduler status, and managing sources.

---

## Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily scrape | 05:00 CET | Scrapes all active sources and enriches new articles |
| Source discovery | Monday 06:00 CET | Discovers and proposes new medical news sources |

---

## License

Private — all rights reserved.

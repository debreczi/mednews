# MedNews

MedNews is a medical news aggregator that scrapes 50+ Hungarian and international medical/pharmaceutical news sources daily, enriches each article with Groq LLM (relevance scoring, AI-generated title, tragic-event detection), and serves them through a FastAPI backend and a Vue 3 SPA frontend with infinite scroll, full-text search, date filters, and social sharing.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Earlier versions not tested |
| Node.js | 20+ | For the Vue frontend |
| Playwright | latest | Chromium browser for JS-rendered sites |
| Groq API key | — | Free tier available at console.groq.com |

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
GROQ_API_KEY=your_groq_api_key_here
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

### 5. Install Playwright browser

```bash
playwright install chromium
```

### 6. Initialize the database

Run Alembic migrations (recommended):
```bash
alembic upgrade head
```

Or use the database module directly:
```bash
python -m backend.database
```

### 7. Seed news sources

```bash
python -m backend.seeds.sources
```

### 8. Start the backend

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 9. Start the frontend (separate terminal)

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

   The script will pause and ask you to edit `/opt/mednews/.env` before continuing. Set `GROQ_API_KEY` and `ADMIN_API_KEY` at minimum.

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
- Installs Playwright + Chromium
- Runs `alembic upgrade head`
- Seeds news sources
- Builds the Vue frontend (`npm run build`)
- Installs and enables the `mednews` systemd service
- Configures nginx as a reverse proxy

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key for LLM enrichment (groq.com) |
| `ADMIN_API_KEY` | Yes | `change_me...` | Secret key for `X-Admin-Key` header on admin endpoints |
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
│   ├── main.py          # FastAPI app entry point
│   ├── database.py      # SQLAlchemy engine + session factory
│   ├── models.py        # ORM models (Article, Source, ...)
│   ├── routers/         # API route handlers (/articles, /search, /admin, /health)
│   ├── scrapers/        # Spider classes (50+ sources)
│   ├── enrichment/      # Groq LLM integration (scoring, title, tragic detection)
│   ├── scheduler/       # APScheduler jobs (daily scrape, weekly discovery)
│   └── seeds/           # Database seed scripts
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components (ArticleCard, SearchBar, ...)
│   │   ├── views/       # Page-level views (Home, Article, Admin)
│   │   └── stores/      # Pinia state management
│   └── dist/            # Production build output (served by nginx)
├── deploy/
│   ├── setup.sh         # Ubuntu 24 LTS bootstrap script
│   ├── mednews.service  # systemd unit file
│   └── nginx.conf       # nginx server block
├── tests/               # pytest test suite
├── alembic/             # Database migration scripts
├── .env.example         # Environment variable template
└── Makefile             # Developer shortcuts
```

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

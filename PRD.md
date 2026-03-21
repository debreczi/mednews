# PRD: MedNews — Hungarian Medical News Aggregator

Version: 1.0 | Status: Active | Owner: Opus Architect Agent

---

## Problem Statement

Hungarian medical IT professionals lack a single, digestible daily source covering medical portals, social media, RSS feeds, and international sources. Reading 50+ sources manually is impractical. Dry medical content is not engaging enough to build a daily reading habit.

## Solution

An automated daily pipeline that scrapes, relevance-scores, and AI-enriches medical news with humorous/cynical Hungarian summaries. Displayed on a fast SPA with infinite scroll, search, and date filtering. Runs on a single Ubuntu 24 VM with no external infrastructure beyond the Groq API.

## Target Users

**Primary**: Hungarian medical IT professionals — software developers, system architects, IT managers, project managers, executives working in healthcare technology.

**Secondary**: Healthcare administrators and medical professionals curious about technology trends.

---

## Functional Requirements

### FR-1: Data Collection
- **FR-1.1** System scrapes minimum 50 sources daily at 05:00 CET
- **FR-1.2** Each article is scored 1–10 for medical IT relevance
- **FR-1.3** Only articles scoring at or above `RELEVANCE_THRESHOLD` (default: 6) are persisted
- **FR-1.4** Sources include: Hungarian portals, RSS feeds, X/Twitter, Facebook, Instagram, LinkedIn, international medical sources (IQVIA, EMA, Medscape, NEJM, etc.)
- **FR-1.5** Duplicate articles (same URL) are never stored twice — enforced by DB unique constraint
- **FR-1.6** Scraping errors are logged and do not halt the entire job

### FR-2: AI Enrichment
- **FR-2.1** Every saved article receives a MedNews title (humorous/cynical, in Hungarian, max 80 chars)
- **FR-2.2** Every saved article receives a summary (humorous, 2–3 sentences, in Hungarian)
- **FR-2.3** Tragic news (death, tragedy) receives a sensitive, respectful summary — no humor
- **FR-2.4** Every saved article receives a link text (Hungarian CTA, max 40 chars, includes original title)
- **FR-2.5** Tragic detection uses a keyword pre-check before calling Groq (saves tokens)
- **FR-2.6** Groq model: `llama-3.3-70b-versatile` primary, `llama-3.1-8b-instant` fallback on rate limit
- **FR-2.7** Failed enrichment is retried up to 3 times; on final failure, `mednews_title` = `original_title`
- **FR-2.8** Articles sent to Groq in batches to reduce API calls

### FR-3: API
- **FR-3.1** `GET /articles` returns cursor-paginated list (25 per page, `?after=<id>`)
- **FR-3.2** `GET /articles/{id}` returns a single article
- **FR-3.3** `GET /search?q=&from_date=&to_date=` returns filtered articles using FTS5
- **FR-3.4** API response time < 200ms for paginated article list (1000 articles in DB)
- **FR-3.5** Admin endpoints protected by `X-Admin-Key` header

### FR-4: Frontend SPA
- **FR-4.1** Loads initial 25 articles on page load
- **FR-4.2** Infinite scroll: loads next 25 articles when user reaches 80% scroll depth
- **FR-4.3** Search bar filters articles with 300ms debounce
- **FR-4.4** Date filter works independently and combined with search
- **FR-4.5** Each article card displays: MedNews title, summary, original link with CTA text, image (or placeholder), date, star rating (score/2), share buttons
- **FR-4.6** Share buttons: LinkedIn, X (Twitter), Facebook, MS Teams deep link, copy-to-clipboard
- **FR-4.7** Frontend is responsive and usable on mobile (min 375px width)
- **FR-4.8** All UI labels, buttons, and messages in Hungarian
- **FR-4.9** Admin page at `/admin`: source list (enable/disable), log viewer, manual scrape trigger

### FR-5: Scheduling
- **FR-5.1** Daily scrape job runs at 05:00 CET via APScheduler
- **FR-5.2** Weekly source auto-discovery job runs via APScheduler
- **FR-5.3** Manual scrape trigger available via `POST /admin/trigger-scrape`
- **FR-5.4** Source list updated on each run (new sources added, inactive ones flagged)

### FR-6: Logging
- **FR-6.1** Scraping audit log: start time, end time, source, articles found, articles saved, errors
- **FR-6.2** API call log: endpoint, timestamp, response time, status code
- **FR-6.3** Groq API log: model, tokens used, cost estimate, article_id
- **FR-6.4** Logs written to both SQLite `audit_log` table and rotating files in `logs/`

---

## Non-Functional Requirements

- **NFR-1** Deployable on Ubuntu 24 LTS VM (minimum: 2 vCPU, 4GB RAM)
- **NFR-2** No external services beyond Groq API (no Redis, no external message queue)
- **NFR-3** From bare Ubuntu to running service in under 30 minutes via `deploy/setup.sh`
- **NFR-4** SQLite DB survives service restart without data loss
- **NFR-5** Frontend first meaningful paint < 2 seconds on a 4G connection
- **NFR-6** `RELEVANCE_THRESHOLD` configured in `.env` / `config.py` — never hardcoded

---

## Acceptance Criteria

```yaml
acceptance_criteria:
  data_collection:
    - id: AC-1
      description: "Cron triggers at 05:00 CET daily"
      test: "APScheduler config has CronTrigger(hour=5, timezone='Europe/Budapest')"

    - id: AC-2
      description: "Minimum 50 spider classes exist"
      test: "count of spider classes in backend/scraper/spiders/ >= 50"

    - id: AC-3
      description: "No articles below threshold in DB"
      test: "SELECT COUNT(*) FROM articles WHERE relevance_score < 6 == 0"

    - id: AC-4
      description: "Duplicate URLs rejected"
      test: "Inserting duplicate URL raises IntegrityError; table count unchanged"

  enrichment:
    - id: AC-5
      description: "All saved articles have mednews_title"
      test: "SELECT COUNT(*) FROM articles WHERE mednews_title IS NULL == 0"

    - id: AC-6
      description: "Tragic news summary contains no humor markers"
      test: "Unit test: tragic keywords in input → humor_flag=False in Groq prompt"

    - id: AC-7
      description: "Enrichment failure falls back to original_title"
      test: "Mock Groq returning 500 x3 → article.mednews_title == article.original_title"

  api:
    - id: AC-8
      description: "GET /articles returns max 25 items with cursor"
      test: "Response JSON: len(data.articles) <= 25 and data.next_cursor present"

    - id: AC-9
      description: "Search returns only matching articles"
      test: "GET /search?q=kardiológia returns articles containing that term only"

    - id: AC-10
      description: "API response < 200ms"
      test: "pytest-benchmark: mean response time < 0.2s with 1000 articles seeded"

  frontend:
    - id: AC-11
      description: "Infinite scroll triggers at 80% depth"
      test: "Vitest: IntersectionObserver mock triggers load at threshold=0.8"

    - id: AC-12
      description: "Share buttons present on each card"
      test: "Vitest: ArticleCard renders ShareButtons with 4 platform buttons"

    - id: AC-13
      description: "Date filter hides out-of-range articles"
      test: "E2E: set from_date, articles before that date not shown"

  deployment:
    - id: AC-14
      description: "setup.sh completes on fresh Ubuntu 24"
      test: "Manual verification on clean VM: script exits 0, service is active"

    - id: AC-15
      description: "systemd service auto-restarts within 5 seconds"
      test: "kill uvicorn PID → service status shows active within 5 seconds"
```

---

## Out of Scope (V1)

- Email newsletter / digest emails
- HTTPS / Let's Encrypt (can be added post-deploy with Certbot)
- Per-user accounts or personalization
- Article rating by users (thumbs up/down)
- Push notifications

---

## Mockup Reference

The UI must match `Mockup/mednews.html` exactly. Vue components are built from that file.
Sample data and canonical field names: `Mockup/articles.json`

---

*Last updated: 2026-03-21 | By: Opus Architect Agent*

# MedNews — Requirements & Q&A

## Introduction

A service that scrapes Hungarian medical news from the internet and writes a daily digest in Hungarian, displayed on a web page. The service reflects daily happenings in medical news — especially IT and business news related to the medical industry. Updated daily so users always have access to the latest information in medical IT.

**Primary audience**: Professionals working in medical IT — software developers, project managers, business developers, creatives, and executives in the medical IT industry.

---

## Page Layout

- **Sticky header**: logo (`M̶a̶edNews`) top-left, search bar top-right
- **Filters**: date filter to narrow articles by publication date
- **Main content**: article cards in a grid, descending by date
- **Article card contents**:
  - Hero image (fallback to source logo if none)
  - Date badge
  - Original title (muted styling)
  - MedNews title (humorous/cynical, Playfair Display font)
  - Star rating (relevance_score / 2 → 1–5 stars)
  - AI-generated summary
  - Source link with Hungarian call-to-action text
  - Share buttons: LinkedIn, X (Twitter), Facebook, Microsoft Teams
- **Infinite scroll**: 25 articles on first load, 25 more per scroll batch (triggers at 80% depth)
- **Footer**: contact, privacy policy, ToS, RSS

---

## Data Format

Articles stored in SQLite with the following fields:

| Field | Description |
|-------|-------------|
| `original_title` | Original title from the source |
| `mednews_title` | AI-generated humorous/cynical title in Hungarian (max 80 chars) |
| `summary` | AI-generated concise summary (2–3 sentences, humorous; respectful for tragic news) |
| `link_text` | CTA text in Hungarian, includes original title (max 40 chars) |
| `source_text` | Display text for the source link |
| `image_url` | Image URL (nullable; null → source logo placeholder) |
| `date_collected` | Timestamp when article was collected |
| `date_published` | Original publication date of the article |
| `relevance_score` | Relevance score 1–10 (only score 6+ are saved) |
| `is_tragic` | Boolean flag; when true, AI omits humor from summary |
| `enrichment_status` | `pending` / `complete` / `failed` |

---

## Operations

### On First Run
- Collect at least 50 sources: Hungarian medical portals, news sites, blogs, social media (X, Facebook, Instagram, LinkedIn), RSS feeds, and important international sources (IQVIA, EMA, Medscape, NEJM, etc.)
- Scrape at least 100 articles on initialization

### Daily Cron Job (05:00 CET)
1. Update source list (add new sources, flag inactive ones)
2. Scrape all sources for new articles
3. Score each article 1–10 for relevance; discard anything below threshold (default: 6)
4. AI enrichment via Groq API (batch calls):
   - Generate MedNews title (humorous/cynical)
   - Generate summary (humorous; sensitive if tragic)
   - Generate link text (Hungarian CTA)
   - Pre-check tragic keywords before Groq call (saves tokens)
5. Extract image URLs (no download — store URL only)
6. Save to database

### Source Auto-Discovery (Weekly)
- AI-powered search for new Hungarian medical news sources
- Cross-reference against existing sources table
- Add newly found active sources, flag inactive ones
- Log results to audit_log

---

## Technology Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Database | SQLite + SQLAlchemy + Alembic | Zero infrastructure, FTS5 for native search, simple backup |
| API Backend | FastAPI + Uvicorn | Async-native for parallel Groq calls, auto-docs |
| Scraping | Scrapy + scrapy-playwright | Handles JS-rendered pages (social media) |
| Scheduler | APScheduler (in-process) | No Redis/Celery needed for a single daily job |
| Frontend | Vue 3 + Vite + Tailwind CSS | Matches mockup design, small bundle, great infinite scroll support |
| State Management | Pinia | Official Vue store, minimal boilerplate |
| AI Enrichment | Groq API (`llama-3.3-70b-versatile`) | Fast, cost-effective, supports Hungarian |
| Logging | SQLite audit_log + rotating file logs | Simple, queryable, no extra infrastructure |
| Deployment | systemd + Nginx + Ubuntu 24 | One-command setup via `deploy/setup.sh` |

---

## Design Tokens (from Mockup)

Reference: `Mockup/mednews.html`

```
bg-primary:       #F7F5F0   (page background)
bg-card:          #FFFFFF
bg-header:        #1A2332   (sticky dark header)
bg-footer:        #151D28
accent-teal:      #0D9488
accent-teal-light #14B8A6
accent-teal-dark: #0F766E
text-primary:     #1E293B
text-secondary:   #475569
text-muted:       #94A3B8
radius:           14px
```

Fonts: `Playfair Display` (article titles), `Source Sans 3` (body), `JetBrains Mono` (meta/technical)
Logo: `M̶a̶edNews` — strikethrough "a" styling, teal gradient icon box

---

## Q&A Record

| # | Question | Answer |
|---|----------|--------|
| Q1 | Frontend framework preference? | Vue 3 + Vite + Tailwind CSS |
| Q2 | Admin panel? | Yes — simple web admin page at `/admin` (source list, log viewer, manual scrape trigger) |
| Q3 | Access control? | Public — no login required |
| Q4 | V1 extra features? | Source auto-discovery (AI periodically searches for new Hungarian medical news sources) |
| Q5 | Groq API key ready? | Yes — configure in `.env` as `GROQ_API_KEY` |
| Q6 | UI language? | Hungarian throughout; reference mockup at `Mockup/mednews.html` |
| Q7 | Article retention policy? | Forever — never delete articles |
| Q8 | Who compiles the source list? | Agents research and select all 50+ sources |

---

## Acceptance Criteria Summary

| AC ID | Description |
|-------|-------------|
| AC-1 | Cron runs at 05:00 CET (`Europe/Budapest` timezone) |
| AC-2 | At least 50 spider classes exist |
| AC-3 | No article in DB has relevance_score < threshold |
| AC-4 | Duplicate URLs rejected (DB unique constraint) |
| AC-5 | Every saved article has a non-null `mednews_title` |
| AC-6 | Tragic articles receive no humor markers in summary |
| AC-7 | Enrichment failure (3x) falls back to original_title |
| AC-8 | GET /articles returns max 25 items per page |
| AC-9 | Search endpoint filters correctly |
| AC-10 | API response < 200ms with 1000 articles in DB |
| AC-11 | Infinite scroll triggers at 80% scroll depth |
| AC-12 | Each card has 4 share buttons (LinkedIn, X, Facebook, Teams) |
| AC-13 | Date filter correctly hides out-of-range articles |
| AC-14 | `setup.sh` completes without errors on fresh Ubuntu 24 |
| AC-15 | systemd service auto-restarts within 5 seconds after crash |

---

*Last updated: 2026-03-21 | By: Sonnet Orchestrator*

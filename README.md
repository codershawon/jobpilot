<h1 align="center">JobPilot AI</h1>
<p align="center"><b>AI-powered job search copilot for Bangladesh</b> — upload your CV once, get matched circulars from BDjobs & government portals, and generate tailored cover letters in one click.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Render-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

<p align="center">
  🔗 <b><a href="https://jobpilot-plum-omega.vercel.app">Live demo</a></b>
</p>

---

## Why JobPilot?

Job hunting in Bangladesh is scattered — BDjobs for private roles, Teletalk/AllJobs for government circulars, RSS feeds, and endless Facebook groups. Candidates re-read the same requirements hundreds of times and hand-write every cover letter.

JobPilot turns that into one flow: **CV in → ranked, deadline-aware job list out → application drafted.**

## ✨ Features

- **📄 CV parsing (PDF/DOCX)** — an LLM extracts skills, experience, and location into a structured profile. No forms to fill.
- **🕸️ Multi-source job ingestion** — custom Python scrapers for **BDjobs**, **Teletalk AllJobs (government circulars)**, and curated **RSS sources**, normalized into one schema.
- **🎯 Skill match scoring** — every circular is scored against your parsed profile, so the best fits rise to the top.
- **⏰ Deadline intelligence** — deadlines are detected per circular; urgent ones get highlighted badges and **Telegram alerts**.
- **✍️ Apply Studio** — one-click tailored **cover letter and cold-email drafts** for any circular.
- **📋 Application tracker** — a Kanban board to move applications through Saved → Applied → Interview → Offer.
- **🔗 Smart social search links** — ToS-safe deep search links into LinkedIn and Facebook (no scraping of either platform).
- **🔁 Resilient LLM router** — automatic fallback across providers, so one API outage never breaks parsing or drafting.
- **🔐 Auth & persistence** — Clerk authentication; profiles and applications persist in Postgres, so you upload your CV once.

## 🏗️ Architecture

```
                      ┌──────────────────────┐
                      │   Next.js frontend   │   Vercel
                      │   (Clerk auth, UI)   │
                      └──────────┬───────────┘
                                 │  REST / JSON
                      ┌──────────▼───────────┐
                      │   FastAPI backend    │   Render (Docker)
                      │  /cv  /pipeline  ... │
                      └───┬──────┬──────┬────┘
                          │      │      │
             ┌────────────▼─┐ ┌──▼────────────┐ ┌─▼─────────────┐
             │  LLM router  │ │   Scrapers    │ │  Telegram bot │
             │  (fallback)  │ │ BDjobs · Govt │ │ deadline      │
             └──────────────┘ │ RSS · extras  │ │ alerts        │
                              └──────┬────────┘ └───────────────┘
                                     │
                          ┌──────────▼───────────┐
                          │   Neon PostgreSQL    │
                          │  jobs · applications │
                          │  saved searches      │
                          └──────────────────────┘
```

A background **worker** refreshes job sources and recomputes deadlines; responses are **cached** to keep scraping polite and the UI fast. Schema is versioned with **Alembic** migrations.

## 🧰 Tech stack

| Layer      | Choice                                                        |
| ---------- | ------------------------------------------------------------- |
| Frontend   | Next.js (App Router), TypeScript, Tailwind CSS, Clerk          |
| Backend    | FastAPI, SQLAlchemy + Alembic, background worker, caching      |
| Scraping   | Custom Python scrapers (BDjobs, Teletalk AllJobs, RSS)         |
| AI         | Multi-provider LLM router with automatic fallback              |
| Database   | PostgreSQL on Neon                                             |
| Messaging  | Telegram Bot API (deadline alerts)                             |
| Deployment | Vercel (frontend) · Render + Docker (backend) · Neon (DB)      |

## 📁 Project structure

```
jobpilot/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # cv, pipeline, applications, districts, portals
│   │   ├── services/      # cv_parser, matcher, classifier, deadline,
│   │   │                  # job_fetcher, job_store, telegram, llm/ (router)
│   │   ├── core/          # database, cache, security
│   │   └── worker.py      # background refresh
│   ├── scrapers/          # bdjobs, teletalk_alljobs (govt), rss, extras
│   ├── alembic/           # migrations
│   ├── tests/
│   └── Dockerfile
└── frontend/
    └── src/
        ├── app/           # landing, tracker, sign-in/up
        ├── components/    # JobGrid, ApplyStudio, KanbanBoard, …
        └── hooks/         # useJobPilotApi, useApplications
```

## 🚀 Running locally

**Requirements:** Node.js 20+, Python 3.11+, a PostgreSQL database (free [Neon](https://neon.tech) works).

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # then fill in the values
alembic upgrade head
python run_server.py
```

API runs at `http://localhost:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local # then fill in the values
npm run dev
```

Open `http://localhost:3000`.

### Environment variables

See **`backend/.env.example`** and **`frontend/.env.example`** for the full lists. The essentials:

| Variable (backend)        | Purpose                           |
| ------------------------- | ---------------------------------- |
| `DATABASE_URL`            | Neon PostgreSQL connection string  |
| LLM provider API key(s)   | CV parsing & cover-letter drafts   |
| `TELEGRAM_BOT_TOKEN` / chat id | Deadline alerts               |

| Variable (frontend)                  | Purpose                  |
| ------------------------------------ | ------------------------- |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`  | Clerk auth (public)       |
| `CLERK_SECRET_KEY`                   | Clerk auth (server)       |
| `NEXT_PUBLIC_API_URL`                | FastAPI base URL          |

## 🧪 Tests

```bash
cd backend
pytest
```

Covers the CV parser today; matcher and scraper tests are on the roadmap.

## ☁️ Deployment

- **Frontend** — Vercel; every push to `main` deploys.
- **Backend** — Render via the included `Dockerfile`. *Note: on Render's free tier the first request after idle takes ~30–50s (cold start).*
- **Database** — Neon serverless PostgreSQL.

## 🗺️ Roadmap

- [ ] Saved-search UI on top of the existing `saved_searches` schema
- [ ] Semantic matching with pgvector embeddings (beyond keyword scoring)
- [ ] Matcher + scraper test coverage, GitHub Actions CI
- [ ] More sources via official job APIs
- [ ] Demo GIF & screenshots in this README

## ⚖️ Honest scope

JobPilot links out to LinkedIn and Facebook with smart search URLs — it deliberately does **not** scrape either platform (ToS). Scraped sources are public job listings, fetched politely with caching.

## 📄 License

MIT © [Shawon Barua](https://shawonbarua.me) · [LinkedIn](https://www.linkedin.com/in/dev-shawon) · [GitHub](https://github.com/codershawon)


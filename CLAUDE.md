# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Monorepo structure

```
Auto-Apply/
├── backend/    # Python — FastAPI server + CLI pipeline
├── frontend/   # React 18 + Vite + Tailwind
└── .venv/      # Shared Python venv (project root)
```

## Running the project

```powershell
# First time — create venv and install Python deps
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt

# CLI (run from backend/ so relative paths resolve correctly)
cd backend
..\.venv\Scripts\python main.py

# Web server — serves built frontend at http://localhost:8000
cd backend
..\.venv\Scripts\uvicorn api.server:app --port 8000 --reload

# Frontend dev server (hot reload, proxies /api to uvicorn)
cd frontend
npm run dev          # http://localhost:5173

# Build frontend for production
cd frontend
npm run build        # outputs to frontend/dist/
```

Syntax-check all Python files:
```powershell
cd backend
python -c "import ast, pathlib; [ast.parse(f.read_text(encoding='utf-8')) for f in pathlib.Path('.').rglob('*.py') if '.git' not in str(f) and '__pycache__' not in str(f) and '.venv' not in str(f)]"
```

## Architecture

The app has two interfaces over the same Python pipeline: a CLI (`main.py`) and a FastAPI web server (`api/`).

```
backend/
  main.py                         # CLI — nine sequential steps, sole user-interaction point
  config.py                       # All tuneable values; secrets loaded from .env
  │
  ├── api/server.py               # FastAPI app; serves frontend/dist/ in production
  ├── api/routes/jobs.py          # GET /api/jobs, POST /api/jobs/scrape (SSE stream)
  ├── api/routes/process.py       # POST /api/process (SSE) — AI + DOCX generation per job
  ├── api/routes/email.py         # POST /api/email/send
  ├── api/routes/config_routes.py # GET/PUT /api/config, CV + data-lake file upload
  │
  ├── scraper/filter_options.py   # Static dicts: display label → URL param value
  ├── scraper/job_scraper.py      # Builds GET URLs, scrapes via requests+BS4; accepts progress_cb
  │
  ├── state/job_store.py          # Loads/saves hkust_jobs.csv; dedup keyed on (company, job_title)
  │
  ├── ai/cv_tailor.py             # Calls Dashscope (OpenAI-compat) to rewrite CV text
  ├── ai/cover_letter_gen.py      # Same client; generates cover letter body only
  │
  ├── document/cv_builder.py      # Plain-text AI output → DOCX (ALL-CAPS headings, "- " bullets)
  ├── document/letter_builder.py  # Wraps AI body with salutation/sign-off → DOCX
  │
  └── mailer/outlook_sender.py    # Win32 Outlook COM — attaches CV + cover letter DOCX, sends
```

**Key data flow:** filters dict → `scrape_jobs(filters, pages)` → list of job dicts → AI functions receive the raw job dict (`details`, `company`, `job_title`, `job_nature`) → document builders write to `output/cv/` and `output/cover_letters/` → mailer reads those paths back.

## Configuration

All tuneable values are in `backend/config.py` (gitignored — copy from `backend/config.py.example` to get started). Secrets are in `backend/.env` (loaded by `python-dotenv`). If `DASHSCOPE_API_KEY` is missing, `config.py` raises `KeyError` on import — intentional.

The Dashscope API is called via the **OpenAI Python SDK** pointed at `https://dashscope.aliyuncs.com/compatible-mode/v1`. Thinking is disabled via `extra_body={"enable_thinking": False}`.

## HKUST job board scraping

- Authentication: `PHPSESSID` session cookie injected into every `requests.Session`. Cookie expires — if scraping returns 0 results, update it in `config.py` or via the Settings page.
- Filter URL params: `BN[]` (business nature), `JN[]` (job nature), `EMT[]` (employment type), `WL[]` (working location), `awards[]` (qualification), `EM[]` (employment mode), `L[]` (language). Full mapping in `scraper/filter_options.py`.
- Pagination: appending `&page=N` to the filter URL. If a page returns 0 listings, the scraper stops early.
- Detail pages: email extracted from `a.red_link[href^="mailto:"]`, website from `a.red_link[href^="https://"]`.

## Document generation

CV builder parses AI output treating ALL-CAPS lines as section headings and `"- "` lines as bullets. Keep the AI prompt and parser in sync if either changes.

Cover letter builder adds salutation (`Dear {company} Recruitment Team,`) and sign-off (`Best Regards, {USER_NAME}`) around the AI body. The AI prompt explicitly excludes these.

## SSE streaming (web only)

`scraper/job_scraper.py::scrape_jobs()` accepts an optional `progress_cb` parameter (default `None` — CLI doesn't use it). The API routes pass a thread-safe callback that enqueues JSON events consumed by `sse_starlette.sse.EventSourceResponse`.

# Auto-Apply

Automated job application tool for the HKUST Career Portal. Scrapes filtered job listings, uses AI to tailor your CV and write a personalised cover letter per role, then auto-sends application emails where possible or gives you the direct apply link for everything else.

Available as both a **CLI** and a **web UI** (React + FastAPI).

---

## Project Structure

```
Auto-Apply/
├── backend/                        # Python — CLI + FastAPI server
│   ├── api/
│   │   ├── server.py               # FastAPI app; serves frontend/dist/ in production
│   │   └── routes/
│   │       ├── config_routes.py    # GET/PUT /api/config, file uploads
│   │       ├── email.py            # POST /api/email/send
│   │       ├── jobs.py             # GET /api/jobs, POST /api/jobs/scrape (SSE)
│   │       └── process.py          # POST /api/process (SSE) — AI + DOCX per job
│   ├── ai/
│   │   ├── cover_letter_gen.py     # Cover letter generation via Deepseek
│   │   └── cv_tailor.py            # CV tailoring via Deepseek
│   ├── document/
│   │   ├── cv_builder.py           # Builds tailored CV as DOCX
│   │   └── letter_builder.py       # Builds cover letter as DOCX
│   ├── mailer/
│   │   └── outlook_sender.py       # Sends emails via Outlook COM (Win32)
│   ├── scraper/
│   │   ├── filter_options.py       # All HKUST filter labels and URL values
│   │   └── job_scraper.py          # requests + BeautifulSoup scraper
│   ├── state/
│   │   └── job_store.py            # CSV load / save / deduplication
│   ├── utils/
│   │   └── helpers.py              # Shared utilities
│   ├── data/                       # Your CV and data lake (not committed)
│   │   ├── my_cv.docx
│   │   └── data_lake.md
│   ├── output/                     # Generated documents (not committed)
│   │   ├── cv/
│   │   └── cover_letters/
│   ├── config.py                   # All configuration variables
│   ├── main.py                     # CLI entry point
│   └── requirements.txt
│
├── frontend/                       # React 18 + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js           # fetch wrappers + SSE helpers
│   │   ├── components/             # StatusBadge, ProgressLog, FilterPanel, JobTable
│   │   └── pages/                  # Dashboard, Scrape, Jobs, Settings
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .venv/                          # Shared Python venv (not committed)
├── .gitignore
├── CLAUDE.md
└── README.md
```

---

## Features

- **Filter-first workflow** — pick industry, job type, location, employment mode, and more before scraping
- **AI-tailored documents** — Deepseek `deepseek-chat` rewrites your CV and cover letter for each specific role
- **Smart apply routing** — auto-sends via Outlook if the recruiter's email is listed; shows the external link and your documents otherwise
- **Persistent job tracking** — CSV state file deduplicates across runs and records what you've applied to
- **Web UI** — Dashboard, Scrape, Jobs, and Settings pages with live SSE progress during scraping and AI generation

---

## Setup

### 1. Clone and create the virtual environment

```powershell
git clone <repo-url>
cd Auto-Apply
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt
```

### 2. Configure secrets — `backend/.env`

```
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3. Configure settings — `backend/config.py`

| Variable | What to set |
|----------|-------------|
| `SESSION_COOKIE` | Your HKUST portal `PHPSESSID` — grab it from browser DevTools → Application → Cookies |
| `USER_NAME` | Your full name (used in document headers and email sign-off) |
| `USER_EMAIL` | Your email address (used in cover letter header) |
| `BCC_EMAIL` | Optional BCC on outgoing emails (leave `""` to disable) |
| `CV_FILE` | Path to your source CV DOCX (default: `data/my_cv.docx`) |
| `DATA_LAKE_FILE` | Path to your personal info file (default: `data/data_lake.md`) |
| `DEFAULT_PAGES` | Default page range shown at scrape prompt (default: `1-3`) |

### 4. Add your documents

- Copy your CV to `backend/data/my_cv.docx`
- Fill in `backend/data/data_lake.md` with background info the AI can draw on

---

## Usage

### Web UI (recommended)

```powershell
# Terminal 1 — backend
cd backend
..\.venv\Scripts\uvicorn api.server:app --port 8000 --reload

# Terminal 2 — frontend dev server (optional, for hot reload)
cd frontend
npm run dev
```

Open **http://localhost:8000** (production build) or **http://localhost:5173** (dev server).

Build the frontend for production:
```powershell
cd frontend && npm run build
```

### CLI

```powershell
cd backend
..\.venv\Scripts\python main.py
```

The CLI walks through nine steps: filter selection → scrape → display → select → AI processing → review → confirm → send emails → manual apply links.

---

## Requirements

- Windows (Outlook COM required for email sending)
- Microsoft Outlook installed and configured with a send-capable account
- Python 3.10+
- Node.js 18+ (for frontend)
- A valid HKUST student/staff session cookie
- A Deepseek API key

---

## Notes

- The `PHPSESSID` cookie expires periodically. If scraping returns zero results, grab a fresh cookie from your browser, or update it directly on the **Settings** page of the web UI.
- Output documents are saved as DOCX to `backend/output/`. Open in Word to export to PDF if needed.
- The CSV state file (`backend/hkust_jobs.csv`) persists across runs. Delete it to start fresh.

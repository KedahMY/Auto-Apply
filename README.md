# Auto-Apply

Automated job application tool for the HKUST Career Portal. Scrapes filtered job listings, uses AI to tailor your CV and write a personalised cover letter per role, then auto-sends application emails where possible or gives you the direct apply link for everything else.

---

## Features

- **Filter-first workflow** — pick industry, job type, location, employment mode, and more before scraping
- **AI-tailored documents** — Dashscope `qwen3.6-flash` rewrites your CV and cover letter for each specific role
- **Smart apply routing** — auto-sends via Outlook if the recruiter's email is listed; shows the external link and your documents otherwise
- **Persistent job tracking** — CSV state file deduplicates across runs and records what you've applied to
- **Modular codebase** — one `config.py` controls everything; each concern lives in its own package

---

## Project Structure

```
Auto-Apply/
├── .env                        # API key (never commit this)
├── config.py                   # All configuration variables
├── main.py                     # Entry point — run this
│
├── scraper/
│   ├── filter_options.py       # All HKUST filter labels and URL values
│   └── job_scraper.py          # requests + BeautifulSoup scraper
│
├── ai/
│   ├── cv_tailor.py            # CV tailoring via Dashscope
│   └── cover_letter_gen.py     # Cover letter generation via Dashscope
│
├── document/
│   ├── cv_builder.py           # Builds tailored CV as DOCX
│   └── letter_builder.py       # Builds cover letter as DOCX
│
├── mailer/
│   └── outlook_sender.py       # Sends emails via Outlook COM (Win32)
│
├── state/
│   └── job_store.py            # CSV load / save / deduplication
│
├── utils/
│   └── helpers.py              # Shared utilities
│
├── data/
│   ├── my_cv.docx              # Your CV (you provide this)
│   └── data_lake.md            # Extra personal info for the AI
│
└── output/
    ├── cv/                     # Tailored CVs (auto-generated)
    └── cover_letters/          # Cover letters (auto-generated)
```

---

## Setup

### 1. Clone and create the virtual environment

```bash
git clone <repo-url>
cd Auto-Apply
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure secrets — `.env`

```
DASHSCOPE_API_KEY=sk-your-key-here
```

### 3. Configure settings — `config.py`

| Variable | What to set |
|----------|-------------|
| `SESSION_COOKIE` | Your HKUST portal `PHPSESSID` — grab it from browser DevTools → Network tab while on the job board |
| `USER_NAME` | Your full name (used in document headers and email sign-off) |
| `USER_EMAIL` | Your email address (used in cover letter header) |
| `BCC_EMAIL` | Optional BCC on outgoing emails (leave `""` to disable) |
| `CV_FILE` | Path to your source CV DOCX (default: `data/my_cv.docx`) |
| `DATA_LAKE_FILE` | Path to your personal info file (default: `data/data_lake.md`) |
| `DEFAULT_PAGES` | Default page range shown at scrape prompt (default: `1-3`) |

### 4. Add your documents

- Copy your CV to `data/my_cv.docx`
- Fill in `data/data_lake.md` with background info the AI can draw on (achievements, goals, preferred roles, etc.)

---

## Usage

```bash
.venv\Scripts\python main.py
```

The tool walks you through nine steps:

| Step | What happens |
|------|-------------|
| 1 | **Filter selection** — choose industry, job type, location, mode, language, keyword |
| 2 | **Scrape** — fetches matching jobs from the HKUST portal |
| 3 | **Job list** — displays results with apply method (Email / Manual) per role |
| 4 | **Select** — pick job numbers (`1,3-5`), `all`, or `back` to re-filter |
| 5 | **AI processing** — tailors CV and writes cover letter for each selected role |
| 6 | **Review** — opens output folders in Explorer; press Enter when ready |
| 7 | **Confirm** — shows exactly which roles get auto-emailed vs manual |
| 8 | **Send** — emails sent via Outlook with tailored CV + cover letter attached |
| 9 | **Manual links** — external apply URLs + document paths for non-email roles |

---

## Requirements

- Windows (Outlook COM required for email sending)
- Microsoft Outlook installed and configured with a send-capable account
- Python 3.10+
- A valid HKUST student/staff session cookie
- A Dashscope API key

---

## Notes

- The `PHPSESSID` session cookie expires periodically. If scraping returns zero results or redirects to login, grab a fresh cookie from your browser.
- Output documents are saved as DOCX. Open in Word and export to PDF manually if needed, or set `save_pdf=True` in `document/letter_builder.py` (requires `docx2pdf`).
- The CSV state file (`hkust_jobs.csv`) persists across runs. Delete it to start fresh.

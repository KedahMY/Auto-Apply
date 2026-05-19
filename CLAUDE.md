# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

```bash
# Create venv and install dependencies (first time)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# Run
.venv\Scripts\python main.py
```

There are no tests or linter configs. Syntax-check all Python files with:
```bash
python -c "import ast, pathlib; [ast.parse(f.read_text(encoding='utf-8')) for f in pathlib.Path('.').rglob('*.py') if '.git' not in str(f) and '__pycache__' not in str(f)]"
```

## Architecture

The app is a linear CLI pipeline. `main.py` orchestrates nine sequential steps and is the only file with user interaction.

```
main.py
  │
  ├── scraper/filter_options.py   # Static dicts: display label → URL param value
  ├── scraper/job_scraper.py      # Builds GET URLs with filter params, scrapes via requests+BS4
  │
  ├── state/job_store.py          # Loads/saves hkust_jobs.csv, deduplication keyed on (company, job_title)
  │
  ├── ai/cv_tailor.py             # Calls Dashscope (OpenAI-compat endpoint) to rewrite CV text
  ├── ai/cover_letter_gen.py      # Same client, generates cover letter body only (no salutation/sign-off)
  │
  ├── document/cv_builder.py      # AI output (plain text with ALL-CAPS headings + "- " bullets) → DOCX
  ├── document/letter_builder.py  # Adds salutation, sign-off, formatting around AI body → DOCX
  │
  └── mailer/outlook_sender.py    # Win32 Outlook COM — attaches CV + cover letter DOCX, sends
```

**Key data flow:** filters dict → `scrape_jobs(filters, pages)` → list of job dicts → AI functions receive the raw job dict (uses `details`, `company`, `job_title`, `job_nature` fields) → document builders write to `output/cv/` and `output/cover_letters/` → mailer reads those paths back.

## Configuration

All tuneable values are in `config.py`. Secrets are in `.env` (loaded by `python-dotenv` at the top of `config.py`). If `DASHSCOPE_API_KEY` is missing from `.env`, `config.py` raises `KeyError` on import — this is intentional.

The Dashscope API is called via the **OpenAI Python SDK** pointed at `https://dashscope.aliyuncs.com/compatible-mode/v1`. Thinking is disabled via `extra_body={"enable_thinking": False}`.

## HKUST job board scraping

- Authentication: `PHPSESSID` session cookie injected into every `requests.Session`. The cookie expires — if scraping returns 0 results, a fresh cookie is needed in `config.py`.
- Filter URL params: `BN[]` (business nature), `JN[]` (job nature), `EMT[]` (employment type), `WL[]` (working location), `awards[]` (qualification), `EM[]` (employment mode), `L[]` (language). All numeric IDs except `awards[]` (bachelor/master/phd) and `EM[]` (FT/PT). Full mapping in `scraper/filter_options.py`.
- Pagination: appending `&page=N` to the filter URL. If a page returns 0 listings, the scraper stops early.
- Detail pages: email is extracted from `a.red_link[href^="mailto:"]`, external website from `a.red_link[href^="https://"]`.

## Document generation

CV builder parses AI output by treating lines that are ALL CAPS as section headings (underlined, bold) and lines starting with `"- "` as bullet points. The AI prompt instructs this format explicitly — keep the prompt and parser in sync if either changes.

Cover letter builder adds salutation (`Dear {company} Recruitment Team,`) and sign-off (`Best Regards, {USER_NAME}`) around the AI-generated body. The AI prompt explicitly excludes these from its output.

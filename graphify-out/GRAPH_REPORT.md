# Graph Report - Auto-Apply  (2026-06-12)

## Corpus Check
- 48 files · ~16,237 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 245 nodes · 311 edges · 40 communities (35 shown, 5 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ac5b7731`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 15 edges
2. `Configuration` - 15 edges
3. `build_letter_docx()` - 8 edges
4. `scrape_jobs()` - 8 edges
5. `main.py CLI` - 8 edges
6. `_process_jobs()` - 7 edges
7. `Input()` - 7 edges
8. `Auto-Apply` - 7 edges
9. `Personal Data Lake` - 6 edges
10. `FastAPI Server` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Personal Data Lake` --shares_data_with--> `frontend API client`  [INFERRED]
  backend/data/data_lake.md → frontend/src/api/client.js
- `Auto-Apply README` --references--> `App Component`  [EXTRACTED]
  README.md → frontend/src/App.jsx
- `frontend API client` --conceptually_related_to--> `backend/utils/helpers.py utilities`  [INFERRED]
  frontend/src/api/client.js → backend/utils/helpers.py
- `_prompt_pages()` --calls--> `parse_page_input()`  [INFERRED]
  backend/main.py → backend/utils/helpers.py
- `_process_jobs()` --calls--> `tailor_cv()`  [INFERRED]
  backend/main.py → backend/ai/cv_tailor.py

## Hyperedges (group relationships)
- **FastAPI Web Interface** — api_server, config, job_scraper, job_store, cv_tailor, cover_letter_gen, cv_builder, letter_builder, outlook_sender [INFERRED 0.85]
- **CLI Interface** — main_cli, config, job_scraper, job_store, cv_tailor, cover_letter_gen, cv_builder, letter_builder, outlook_sender [EXTRACTED 1.00]
- **Frontend Navigation and Routing** — react_app, react_dashboard, react_scrape, react_jobs, react_settings [EXTRACTED 0.75]
- **Frontend Tooling Configs** — config_vite, config_tailwind, config_postcss [INFERRED 0.95]
- **Client APIs used by pages** — js_api_client, react_dashboard, react_jobs, react_scrape, react_settings [INFERRED 0.85]

## Communities (40 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (12): api, cvPreviewUrl(), cvUrl(), letterPreviewUrl(), letterUrl(), processSSE(), scrapeSSE(), FILTER_GROUPS (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (14): generate_email(), _get_client(), Return (subject, body) for a personalised application email.     On any error or, _doc_path(), send_emails(), _docx_to_pdf(), preview_cv(), preview_letter() (+6 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (19): 1. Clone and create the virtual environment, 2. Configure secrets — `backend/.env`, 3. Configure settings — `backend/config.py`, 4. Add your documents, Auto-Apply, CLI, code:block1 (Auto-Apply/), code:powershell (git clone <repo-url>) (+11 more)

### Community 3 - "Community 3"
Cohesion: 0.2
Nodes (18): _check_config(), _confirm_send(), _display_jobs(), main(), _pick_filters(), _pick_multi(), _process_jobs(), _prompt_job_selection() (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): Architecture, code:block1 (# The server is already running — use the mcp__playwright__ ), code:block2 (Auto-Apply/), code:powershell (# First time — create venv and install Python deps), code:powershell (cd backend), code:block5 (backend/), Configuration, Document generation (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.23
Nodes (13): _get_client(), Return a dict mapping paragraph index (str) → rewritten text for bullet paragrap, tailor_cv(), FastAPI Server, Configuration, Cover Letter Gen AI, CV DOCX Builder, CV Tailor AI (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.18
Nodes (14): Personal Data Lake, frontend API client, backend/utils/helpers.py utilities, App Component, Dashboard Component, FilterPanel Component, Jobs Component, JobTable Component (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (11): _apply_replacement(), build_cv_docx(), Replace the text content of a paragraph while preserving all paragraph-level, Copy the original CV DOCX and surgically apply paragraph-level text replacements, _add_para(), build_letter_docx(), _clean_body(), _convert_to_pdf() (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (7): delete_all_jobs(), delete_job(), existing_keys(), is_duplicate(), mark_applied(), mark_letter_done(), save_jobs()

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (9): _build_session(), _build_url(), _parse_detail_page(), _parse_list_page(), Scrape the given page numbers with active filters, return job dicts.      progre, Build a filter-aware paginated URL.      filters keys match the form param names, _safe_get(), scrape_jobs() (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.25
Nodes (5): _df_to_jobs(), get_jobs(), scrape_jobs_stream(), parse_page_input(), Parse a page string like '3' or '1-5' into a list of page numbers.

### Community 11 - "Community 11"
Cohesion: 0.43
Nodes (7): ApplyPatchRequest, ConfigUpdate, JobResponse, ProcessRequest, ScrapeRequest, SendRequest, BaseModel

### Community 12 - "Community 12"
Cohesion: 0.36
Nodes (4): _load_settings(), _save_settings(), update_config(), _update_env_key()

### Community 13 - "Community 13"
Cohesion: 0.32
Nodes (6): _default_body(), _dispatch_outlook(), Connect to a running Outlook instance, retrying on RPC_E_CALL_REJECTED., Send a job application email via Outlook COM.     Returns True on success, False, Send a job application email via Outlook COM.     `subject` / `body` are the AI-, send_application()

### Community 14 - "Community 14"
Cohesion: 0.29
Nodes (6): Background, Career Goals, Extra Info for Applications, Key Strengths, Notable Achievements, Personal Data Lake

### Community 15 - "Community 15"
Cohesion: 0.47
Nodes (5): _call_api(), generate_cover_letter(), _get_client(), Return the body of a personalised cover letter, enforced to ≤250 words., Return the body of a personalised cover letter, enforced to ≤250 words.

## Knowledge Gaps
- **63 isolated node(s):** `Auto-Apply — main entry point.  Run:  python main.py  (use the .venv interpreter`, `Show a numbered list and return selected option values. Enter = skip.`, `Return 0-based indices, or None if user wants to go back to filters.`, `Generate tailored CV + cover letter for each job. Returns enriched job dicts.`, `Return the body of a personalised cover letter, enforced to ≤250 words.` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Configuration` connect `Community 5` to `Community 1`, `Community 3`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 12`, `Community 13`, `Community 15`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `Input()` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 3` to `Community 1`, `Community 9`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `main()` (e.g. with `extract_docx_text()` and `read_text_file()`) actually correct?**
  _`main()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `build_letter_docx()` (e.g. with `_process_jobs()` and `sanitize_filename()`) actually correct?**
  _`build_letter_docx()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Auto-Apply — main entry point.  Run:  python main.py  (use the .venv interpreter`, `Show a numbered list and return selected option values. Enter = skip.`, `Return 0-based indices, or None if user wants to go back to filters.` to the rest of the system?**
  _63 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._
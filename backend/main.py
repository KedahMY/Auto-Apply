"""
Auto-Apply — main entry point.

Run:  python main.py  (use the .venv interpreter)
"""

import os
import sys
import time

import pandas as pd

import config
from utils.helpers import extract_docx_text, read_text_file, parse_page_input
from scraper.job_scraper import scrape_jobs
from scraper.filter_options import FILTER_GROUPS
from state import job_store
from ai.cv_tailor import tailor_cv
from ai.cover_letter_gen import generate_cover_letter
from document.cv_builder import build_cv_docx
from document.letter_builder import build_letter_docx
from mailer import outlook_sender


# ---------------------------------------------------------------------------
# Config guard
# ---------------------------------------------------------------------------

def _check_config():
    errors = []
    if "YOUR_API_KEY" in config.DEEPSEEK_API_KEY:
        errors.append("Set DEEPSEEK_API_KEY in .env")
    if "YOUR_PHPSESSID" in config.SESSION_COOKIE:
        errors.append("Set SESSION_COOKIE (PHPSESSID) in config.py")
    if "Your Full Name" in config.USER_NAME:
        errors.append("Set USER_NAME in config.py")
    if "your@email" in config.USER_EMAIL:
        errors.append("Set USER_EMAIL in config.py")
    if errors:
        print("Configuration incomplete:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Step 1 — Filter selection
# ---------------------------------------------------------------------------

def _pick_multi(label: str, options: dict) -> list[str]:
    """Show a numbered list and return selected option values. Enter = skip."""
    keys = list(options.keys())
    print(f"\n  {label}  (multi-select, Enter to skip / apply all)")
    for i, k in enumerate(keys, 1):
        print(f"    {i:>2}. {k}")
    raw = input("  Select (e.g. 1,3-5) or Enter to skip: ").strip()
    if not raw:
        return []
    selected = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            for idx in range(int(a) - 1, int(b)):
                if 0 <= idx < len(keys):
                    selected.append(options[keys[idx]])
        else:
            idx = int(part) - 1
            if 0 <= idx < len(keys):
                selected.append(options[keys[idx]])
    return selected


def _pick_filters() -> dict:
    print("\n" + "=" * 60)
    print("  STEP 1 — SELECT FILTERS")
    print("  (Press Enter on any filter to include all)")
    print("=" * 60)

    filters: dict = {}
    for label, param, options, _ in FILTER_GROUPS:
        values = _pick_multi(label, options)
        if values:
            filters[param] = values

    kw = input("\n  Keyword search (Enter to skip): ").strip()
    filters["keywords"] = kw

    # Checkboxes
    print("\n  Extra options:")
    if input("    Active jobs only? (y/N): ").strip().lower() == "y":
        filters["AJOB"] = True
    if input("    Non-Chinese speaking students considered? (y/N): ").strip().lower() == "y":
        filters["NCHI"] = True

    return filters


def _summarise_filters(filters: dict) -> str:
    from scraper.filter_options import (
        BUSINESS_NATURE, JOB_NATURE, EMPLOYMENT_TYPE,
        WORKING_LOCATION, QUALIFICATION, EMPLOYMENT_MODE, LANGUAGE,
    )
    reverse = {
        "BN[]": {v: k for k, v in BUSINESS_NATURE.items()},
        "JN[]": {v: k for k, v in JOB_NATURE.items()},
        "EMT[]": {v: k for k, v in EMPLOYMENT_TYPE.items()},
        "WL[]": {v: k for k, v in WORKING_LOCATION.items()},
        "awards[]": {v: k for k, v in QUALIFICATION.items()},
        "EM[]": {v: k for k, v in EMPLOYMENT_MODE.items()},
        "L[]": {v: k for k, v in LANGUAGE.items()},
    }
    parts = []
    for param, lookup in reverse.items():
        vals = filters.get(param, [])
        if vals:
            labels = [lookup.get(v, v) for v in vals]
            parts.append(f"{param.rstrip('[]')}: {', '.join(labels)}")
    if filters.get("keywords"):
        parts.append(f"keyword: \"{filters['keywords']}\"")
    if filters.get("AJOB"):
        parts.append("Active jobs only")
    if filters.get("NCHI"):
        parts.append("Non-Chinese speaking welcome")
    return " | ".join(parts) if parts else "No filters (all jobs)"


# ---------------------------------------------------------------------------
# Step 2 — Scrape
# ---------------------------------------------------------------------------

def _prompt_pages() -> list[int]:
    default = config.DEFAULT_PAGES
    while True:
        raw = input(f"\n  Pages to scrape [{default}]: ").strip() or default
        try:
            pages = parse_page_input(raw)
            if len(pages) > 50:
                ok = input(f"  That's {len(pages)} pages (~{len(pages)*20} jobs). Continue? (y/N): ").strip().lower()
                if ok != "y":
                    continue
            return pages
        except ValueError as e:
            print(f"  Invalid: {e}. Use '3' or '1-5'.")


# ---------------------------------------------------------------------------
# Step 3 — Display job list
# ---------------------------------------------------------------------------

def _display_jobs(jobs_df) -> None:
    W = 114
    print("\n" + "-" * W)
    print(f"{'#':>4}  {'Company':<28}  {'Job Title':<36}  {'Deadline':<12}  {'Method':<6}  Website?")
    print("-" * W)
    for i, (_, row) in enumerate(jobs_df.iterrows(), 1):
        company  = str(row.get("company",   ""))[:27]
        title    = str(row.get("job_title", ""))[:35]
        deadline = str(row.get("deadline",  ""))[:11]
        email    = str(row.get("email",     "")).strip()
        website  = str(row.get("website",   "")).strip()
        method   = "Email" if email else "Manual"
        has_web  = "Yes" if website else "-"
        print(f"{i:>4}  {company:<28}  {title:<36}  {deadline:<12}  {method:<6}  {has_web}")
    print("-" * W)
    print(f"  {len(jobs_df)} job(s) found\n")


# ---------------------------------------------------------------------------
# Step 4 — Job selection
# ---------------------------------------------------------------------------

def _prompt_job_selection(total: int) -> list[int] | None:
    """Return 0-based indices, or None if user wants to go back to filters."""
    while True:
        raw = input(
            "  Select jobs to apply for (e.g. 1,3-5 / 'all' / 'back'): "
        ).strip().lower()
        if raw == "back":
            return None
        if raw == "all":
            return list(range(total))
        try:
            indices = []
            for part in raw.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-", 1)
                    indices.extend(range(int(a) - 1, int(b)))
                else:
                    indices.append(int(part) - 1)
            bad = [i for i in indices if i < 0 or i >= total]
            if bad:
                print(f"  Out of range: {[i+1 for i in bad]}  (valid: 1–{total})")
                continue
            if not indices:
                print("  No jobs selected.")
                continue
            return indices
        except ValueError:
            print("  Invalid format. Try: 2  or  1,3  or  2-5  or  all  or  back")


# ---------------------------------------------------------------------------
# Step 5 — AI processing
# ---------------------------------------------------------------------------

def _process_jobs(selected_jobs: list[dict], cv_text: str, data_lake: str) -> list[dict]:
    """Generate tailored CV + cover letter for each job. Returns enriched job dicts."""
    results = []
    total = len(selected_jobs)
    for i, job in enumerate(selected_jobs, 1):
        company = job.get("company", "?")
        title   = job.get("job_title", "?")
        print(f"\n  [{i}/{total}] {company} — {title}")

        print("    Tailoring CV...", end=" ", flush=True)
        tailored = tailor_cv(cv_text, data_lake, job)
        cv_path  = build_cv_docx(tailored, job)
        print("done")

        print("    Writing cover letter...", end=" ", flush=True)
        letter_body = generate_cover_letter(cv_text, data_lake, job)
        letter_path = build_letter_docx(letter_body, job)
        print("done")

        results.append({**job, "_cv_path": cv_path, "_letter_path": letter_path})
    return results


# ---------------------------------------------------------------------------
# Step 6 — Document review pause
# ---------------------------------------------------------------------------

def _review_documents(results: list[dict]) -> None:
    print("\n" + "=" * 60)
    print("  STEP 6 — REVIEW YOUR DOCUMENTS")
    print("=" * 60)
    for r in results:
        company = r.get("company", "?")
        title   = r.get("job_title", "?")
        print(f"\n  {company} — {title}")
        print(f"    CV:           {r['_cv_path']}")
        print(f"    Cover letter: {r['_letter_path']}")

    # Open the output folders in Explorer so the user can review easily
    for folder in (config.OUTPUT_CV_DIR, config.OUTPUT_LETTER_DIR):
        if os.path.isdir(folder):
            os.startfile(os.path.abspath(folder))

    print("\n  Output folders opened in Explorer. Review the documents above.")
    input("  Press Enter when you are ready to continue...")


# ---------------------------------------------------------------------------
# Step 7 — Send confirmation
# ---------------------------------------------------------------------------

def _confirm_send(results: list[dict]) -> tuple[list[dict], list[dict]]:
    email_jobs  = [r for r in results if str(r.get("email", "")).strip()]
    manual_jobs = [r for r in results if not str(r.get("email", "")).strip()]

    print("\n" + "=" * 60)
    print("  STEP 7 — CONFIRM APPLICATIONS")
    print("=" * 60)

    if email_jobs:
        print(f"\n  Will AUTO-SEND email to {len(email_jobs)} job(s):")
        for r in email_jobs:
            print(f"    • {r.get('company')} — {r.get('job_title')}  →  {r.get('email')}")

    if manual_jobs:
        print(f"\n  MANUAL apply required for {len(manual_jobs)} job(s):")
        for r in manual_jobs:
            site = str(r.get("website", "")).strip() or "job portal"
            print(f"    • {r.get('company')} — {r.get('job_title')}  ({site})")

    if not email_jobs:
        print("\n  No email applications to send.")
        return [], manual_jobs

    confirm = input("\n  Send the emails now? (y/N): ").strip().lower()
    if confirm != "y":
        print("  Cancelled. No emails sent.")
        return [], manual_jobs

    return email_jobs, manual_jobs


# ---------------------------------------------------------------------------
# Step 8 — Send emails
# ---------------------------------------------------------------------------

def _send_emails(email_jobs: list[dict], df) -> None:
    print("\n" + "=" * 60)
    print("  STEP 8 — SENDING EMAILS")
    print("=" * 60)
    for i, job in enumerate(email_jobs, 1):
        company = job.get("company", "?")
        title   = job.get("job_title", "?")
        email   = job.get("email", "")
        print(f"\n  [{i}/{len(email_jobs)}] {company} — {title}")
        print(f"    Sending to {email}...", end=" ", flush=True)

        ok = outlook_sender.send_application(
            email, job, job["_cv_path"], job["_letter_path"]
        )
        if ok:
            print("sent.")
            mask = (df["company"] == company) & (df["job_title"] == title)
            if mask.any():
                job_store.mark_applied(df, df[mask].index[0])
        else:
            print("FAILED (send manually).")

        if i < len(email_jobs):
            time.sleep(5)


# ---------------------------------------------------------------------------
# Step 9 — Manual apply reminder
# ---------------------------------------------------------------------------

def _show_manual_links(manual_jobs: list[dict]) -> None:
    if not manual_jobs:
        return
    print("\n" + "=" * 60)
    print("  STEP 9 — MANUAL APPLICATIONS")
    print("  Use your optimised CV and cover letter for these roles.")
    print("=" * 60)
    for job in manual_jobs:
        company = job.get("company", "?")
        title   = job.get("job_title", "?")
        site    = str(job.get("website", "")).strip() or "(no external link — check HKUST portal)"
        print(f"\n  {company} — {title}")
        print(f"    Apply at:     {site}")
        print(f"    CV:           {job['_cv_path']}")
        print(f"    Cover letter: {job['_letter_path']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  AUTO-APPLY  |  HKUST Career Portal")
    print("=" * 60)

    _check_config()

    # Load user documents once
    try:
        cv_text = extract_docx_text(config.CV_FILE)
    except FileNotFoundError as e:
        print(f"ERROR: {e}\nPlace your CV at '{config.CV_FILE}' (set in config.py).")
        sys.exit(1)
    try:
        data_lake = read_text_file(config.DATA_LAKE_FILE)
    except FileNotFoundError as e:
        print(f"ERROR: {e}\nPlace your data lake at '{config.DATA_LAKE_FILE}' (set in config.py).")
        sys.exit(1)

    print(f"  CV:        {config.CV_FILE}")
    print(f"  Data lake: {config.DATA_LAKE_FILE}")

    df = job_store.load_jobs()

    while True:
        # --- Step 1: filters ---
        filters = _pick_filters()
        summary = _summarise_filters(filters)
        print(f"\n  Active filters: {summary}")

        # --- Step 2: scrape ---
        pages = _prompt_pages()
        print(f"\n  Scraping {len(pages)} page(s)...")
        raw_jobs = scrape_jobs(filters, pages)

        if not raw_jobs:
            print("  No jobs returned. Try different filters or more pages.")
            continue

        # Deduplicate + persist
        existing = job_store.existing_keys(df)
        fresh = [
            j for j in raw_jobs
            if (str(j.get("company", "")), str(j.get("job_title", ""))) not in existing
        ]
        df = job_store.append_jobs(df, fresh)
        job_store.save_jobs(df)
        print(f"  {len(fresh)} new job(s) saved ({len(raw_jobs)-len(fresh)} already known).")

        # Build display frame from this scrape's results (all, not just fresh)
        display_df = pd.DataFrame(raw_jobs).reset_index(drop=True)

        # --- Step 3: display ---
        print(f"\n  STEP 3 — FILTERED JOB LIST  [{summary}]")
        _display_jobs(display_df)

        # --- Step 4: select ---
        print("  STEP 4 — SELECT JOBS")
        selected_indices = _prompt_job_selection(len(display_df))
        if selected_indices is None:
            print("  Going back to filter selection...\n")
            continue

        selected_jobs = [display_df.iloc[i].to_dict() for i in selected_indices]

        # --- Step 5: AI processing ---
        print(f"\n  STEP 5 — GENERATING DOCUMENTS  ({len(selected_jobs)} job(s))")
        results = _process_jobs(selected_jobs, cv_text, data_lake)

        # --- Step 6: review ---
        _review_documents(results)

        # --- Step 7: confirm ---
        email_jobs, manual_jobs = _confirm_send(results)

        # --- Step 8: send ---
        if email_jobs:
            _send_emails(email_jobs, df)

        # --- Step 9: manual links ---
        _show_manual_links(manual_jobs)

        print("\n  Done. Run again to apply for more jobs.")
        break


if __name__ == "__main__":
    main()

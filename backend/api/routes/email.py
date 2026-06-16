import os
from fastapi import APIRouter, HTTPException

import config
from api.models import SendRequest
from ai.email_gen import generate_email
from mailer import outlook_sender
from state import job_store
from utils.helpers import extract_docx_text, read_text_file

router = APIRouter()


@router.post("/email/send")
def send_emails(body: SendRequest):
    df = job_store.load_jobs()
    results = []

    # Load CV + data lake once for AI email personalisation. If either is missing,
    # fall back to empty strings — the sender still works with its boilerplate body.
    try:
        cv_text = extract_docx_text(config.CV_FILE)
    except FileNotFoundError:
        cv_text = ""
    try:
        data_lake = read_text_file(config.DATA_LAKE_FILE)
    except FileNotFoundError:
        data_lake = ""

    for idx in body.row_indices:
        if idx not in df.index:
            results.append({"row_index": idx, "ok": False, "error": "Job not found"})
            continue

        row = df.loc[idx]
        company = str(row.get("company", ""))
        title = str(row.get("job_title", ""))
        email_addr = str(row.get("email", "")).strip()

        if not email_addr:
            results.append({"row_index": idx, "ok": False, "error": "No email address"})
            continue

        cv_file = str(row.get("cv_file", "")).strip()
        letter_file = str(row.get("letter_file", "")).strip()

        if not cv_file:
            results.append({"row_index": idx, "ok": False, "error": "Documents not generated yet — run Process first"})
            continue
        if not letter_file:
            results.append({"row_index": idx, "ok": False, "error": "Cover letter not generated yet — run Process first"})
            continue

        cv_path = os.path.join(config.OUTPUT_CV_DIR, cv_file)
        letter_path = os.path.join(config.OUTPUT_LETTER_DIR, letter_file)

        if not os.path.isfile(cv_path):
            results.append({"row_index": idx, "ok": False, "error": f"CV file missing on disk: {cv_file}"})
            continue
        if not os.path.isfile(letter_path):
            results.append({"row_index": idx, "ok": False, "error": f"Cover letter file missing on disk: {letter_file}"})
            continue

        job_dict = row.to_dict()
        subject, ai_body = generate_email(cv_text, data_lake, job_dict)
        ok, err = outlook_sender.send_application(
            email_addr, job_dict, cv_path, letter_path, subject=subject, body=ai_body
        )

        if ok:
            job_store.mark_applied(df, idx)

        entry = {"row_index": idx, "ok": ok, "company": company, "job_title": title}
        if not ok and err:
            entry["error"] = err
        results.append(entry)

    return {"results": results}

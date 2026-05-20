import os
from fastapi import APIRouter, HTTPException

import config
from api.models import SendRequest
from mailer import outlook_sender
from state import job_store
from utils.helpers import sanitize_filename

router = APIRouter()


def _doc_path(directory: str, company: str, job_title: str, suffix: str) -> str:
    name = f"{sanitize_filename(company)}_{sanitize_filename(job_title)}_{suffix}.docx"
    return os.path.join(directory, name)


@router.post("/email/send")
def send_emails(body: SendRequest):
    df = job_store.load_jobs()
    results = []

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

        cv_path = _doc_path(config.OUTPUT_CV_DIR, company, title, "CV")
        letter_path = _doc_path(config.OUTPUT_LETTER_DIR, company, title, "CoverLetter")

        if not os.path.isfile(cv_path):
            results.append({"row_index": idx, "ok": False, "error": f"CV not found: {os.path.basename(cv_path)}"})
            continue
        if not os.path.isfile(letter_path):
            results.append({"row_index": idx, "ok": False, "error": f"Cover letter not found: {os.path.basename(letter_path)}"})
            continue

        job_dict = row.to_dict()
        ok = outlook_sender.send_application(email_addr, job_dict, cv_path, letter_path)

        if ok:
            job_store.mark_applied(df, idx)

        results.append({"row_index": idx, "ok": ok, "company": company, "job_title": title})

    return {"results": results}

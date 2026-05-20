import asyncio
import json
import os
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

import config
from api.models import ProcessRequest
from ai.cv_tailor import tailor_cv
from ai.cover_letter_gen import generate_cover_letter
from document.cv_builder import build_cv_docx
from document.letter_builder import build_letter_docx
from state import job_store
from utils.helpers import extract_docx_text, read_text_file

router = APIRouter()


@router.post("/process")
async def process_jobs_stream(body: ProcessRequest, request: Request):
    df = job_store.load_jobs()
    valid_indices = [i for i in body.row_indices if i in df.index]
    if not valid_indices:
        raise HTTPException(status_code=422, detail="No valid job indices provided")

    selected_jobs = [df.loc[i].to_dict() for i in valid_indices]

    try:
        cv_text = extract_docx_text(config.CV_FILE)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        data_lake = read_text_file(config.DATA_LAKE_FILE)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def emit(event: dict):
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def run():
        total = len(selected_jobs)
        try:
            for n, (idx, job) in enumerate(zip(valid_indices, selected_jobs), 1):
                company = str(job.get("company", "?"))
                title = str(job.get("job_title", "?"))

                emit({"type": "step", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title, "step": "cv_tailoring"})
                tailored = tailor_cv(cv_text, data_lake, job)

                emit({"type": "step", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title, "step": "cv_building"})
                cv_path = build_cv_docx(tailored, job)
                cv_file = os.path.basename(cv_path)

                emit({"type": "step", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title, "step": "letter_generating"})
                letter_body = generate_cover_letter(cv_text, data_lake, job)

                emit({"type": "step", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title, "step": "letter_building"})
                letter_path = build_letter_docx(letter_body, job)
                letter_file = os.path.basename(letter_path)

                emit({"type": "job_done", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title,
                      "cv_file": cv_file, "letter_file": letter_file})

                job_store.mark_letter_done(df, idx)

            emit({"type": "all_done"})
        except Exception as e:
            emit({"type": "error", "message": str(e)})
        finally:
            emit(None)

    threading.Thread(target=run, daemon=True).start()

    async def generate():
        while True:
            if await request.is_disconnected():
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=1.0)
                if item is None:
                    return
                yield {"data": json.dumps(item)}
            except asyncio.TimeoutError:
                yield {"data": json.dumps({"type": "ping"})}

    return EventSourceResponse(generate())


@router.get("/documents/cv/{filename}")
def download_cv(filename: str):
    path = os.path.join(config.OUTPUT_CV_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        filename=filename)


@router.get("/documents/letter/{filename}")
def download_letter(filename: str):
    path = os.path.join(config.OUTPUT_LETTER_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        filename=filename)

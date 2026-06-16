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
                replacements = tailor_cv(config.CV_FILE, data_lake, job)

                emit({"type": "step", "n": n, "total": total, "row_index": idx,
                      "company": company, "title": title, "step": "cv_building"})
                cv_path = build_cv_docx(replacements, job)
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

                job_store.mark_letter_done(df, idx, cv_file=cv_file, letter_file=letter_file)

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


def _docx_to_pdf(docx_path: str) -> str:
    """Convert a DOCX to PDF using Word COM (pywin32). Returns the PDF path."""
    import pythoncom
    import win32com.client

    pdf_path = docx_path.replace(".docx", ".pdf")
    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(pdf_path)

    # Only re-convert if the DOCX is newer than the cached PDF
    if os.path.isfile(abs_pdf) and os.path.getmtime(abs_pdf) >= os.path.getmtime(abs_docx):
        return pdf_path

    pythoncom.CoInitialize()
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False
        try:
            doc = word.Documents.Open(abs_docx)
            doc.SaveAs(abs_pdf, FileFormat=17)  # 17 = wdFormatPDF
            doc.Close(0)
        finally:
            word.Quit()
    except Exception as exc:
        raise RuntimeError(f"Word COM PDF conversion failed: {exc}") from exc
    finally:
        pythoncom.CoUninitialize()

    return pdf_path


@router.get("/documents/cv/{filename}/preview")
def preview_cv(filename: str):
    docx_path = os.path.join(config.OUTPUT_CV_DIR, filename)
    if not os.path.isfile(docx_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        pdf_path = _docx_to_pdf(docx_path)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(pdf_path, media_type="application/pdf")


@router.get("/documents/letter/{filename}/preview")
def preview_letter(filename: str):
    docx_path = os.path.join(config.OUTPUT_LETTER_DIR, filename)
    if not os.path.isfile(docx_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        pdf_path = _docx_to_pdf(docx_path)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FileResponse(pdf_path, media_type="application/pdf")

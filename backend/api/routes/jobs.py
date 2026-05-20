import asyncio
import json
import threading
from typing import List

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

import config
from api.models import JobResponse, ScrapeRequest
from scraper.job_scraper import scrape_jobs
from state import job_store
from utils.helpers import parse_page_input

router = APIRouter()


def _df_to_jobs(df) -> List[dict]:
    jobs = []
    for idx, row in df.iterrows():
        jobs.append({
            "row_index": int(idx),
            "job_id": str(row.get("job_id", "")),
            "company": str(row.get("company", "")),
            "job_title": str(row.get("job_title", "")),
            "job_nature": str(row.get("job_nature", "")),
            "posting_date": str(row.get("posting_date", "")),
            "deadline": str(row.get("deadline", "")),
            "email": str(row.get("email", "")),
            "website": str(row.get("website", "")),
            "detail_url": str(row.get("detail_url", "")),
            "applied": str(row.get("applied", "False")),
            "letter": str(row.get("letter", "False")),
        })
    return jobs


@router.get("/jobs", response_model=List[JobResponse])
def get_jobs():
    df = job_store.load_jobs()
    return _df_to_jobs(df)


@router.patch("/jobs/{row_index}/apply")
def mark_job_applied(row_index: int):
    df = job_store.load_jobs()
    if row_index not in df.index:
        raise HTTPException(status_code=404, detail="Job not found")
    job_store.mark_applied(df, row_index)
    return {"ok": True}


@router.post("/jobs/scrape")
async def scrape_jobs_stream(body: ScrapeRequest, request: Request):
    try:
        pages = parse_page_input(body.pages)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def progress_cb(event: dict):
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def run():
        try:
            raw_jobs = scrape_jobs(body.filters, pages, progress_cb=progress_cb)
            df = job_store.load_jobs()
            existing = job_store.existing_keys(df)
            fresh = [
                j for j in raw_jobs
                if (str(j.get("company", "")), str(j.get("job_title", ""))) not in existing
            ]
            if fresh:
                df = job_store.append_jobs(df, fresh)
                job_store.save_jobs(df)
            loop.call_soon_threadsafe(queue.put_nowait, {
                "type": "done",
                "new_jobs": len(fresh),
                "total": len(raw_jobs),
                "total_stored": len(df),
            })
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "message": str(e)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

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

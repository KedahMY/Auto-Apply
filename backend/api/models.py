from pydantic import BaseModel
from typing import Optional


class JobResponse(BaseModel):
    row_index: int
    job_id: str
    company: str
    job_title: str
    job_nature: str
    posting_date: str
    deadline: str
    email: str
    website: str
    detail_url: str
    applied: str
    letter: str
    cv_file: Optional[str] = None
    letter_file: Optional[str] = None


class ScrapeRequest(BaseModel):
    filters: dict
    pages: str = "1-3"


class ProcessRequest(BaseModel):
    row_indices: list[int]


class SendRequest(BaseModel):
    row_indices: list[int]


class ApplyPatchRequest(BaseModel):
    pass


class ConfigUpdate(BaseModel):
    dashscope_api_key: Optional[str] = None
    session_cookie: Optional[str] = None
    model_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    bcc_email: Optional[str] = None
    default_pages: Optional[str] = None

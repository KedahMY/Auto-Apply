import json
import os
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File

import config
from api.models import ConfigUpdate

router = APIRouter()

_SETTINGS_PATH = os.path.join("data", "settings.json")


def _load_settings() -> dict:
    if os.path.isfile(_SETTINGS_PATH):
        with open(_SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_settings(settings: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def apply_settings() -> None:
    """Apply persisted settings.json onto the live config module.

    Keys in settings.json match config attribute names, so changes saved via
    the Settings UI survive a server restart. Called once on startup.
    """
    for key, value in _load_settings().items():
        if hasattr(config, key):
            setattr(config, key, value)


def _update_env_key(key: str, value: str) -> None:
    env_path = ".env"
    lines = []
    found = False
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            lines = f.readlines()
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


@router.get("/config")
def get_config():
    return {
        "deepseek_api_key": "***" if config.DEEPSEEK_API_KEY else "",
        "session_cookie": config.SESSION_COOKIE,
        "model_id": config.DEEPSEEK_MODEL_ID,
        "user_name": config.USER_NAME,
        "user_email": config.USER_EMAIL,
        "bcc_email": config.BCC_EMAIL,
        "default_pages": config.DEFAULT_PAGES,
        "cv_file": config.CV_FILE,
        "data_lake_file": config.DATA_LAKE_FILE,
        "cv_exists": os.path.isfile(config.CV_FILE),
        "data_lake_exists": os.path.isfile(config.DATA_LAKE_FILE),
    }


@router.put("/config")
def update_config(body: ConfigUpdate):
    settings = _load_settings()

    if body.deepseek_api_key is not None and body.deepseek_api_key != "***":
        _update_env_key("DEEPSEEK_API_KEY", body.deepseek_api_key)
        config.DEEPSEEK_API_KEY = body.deepseek_api_key

    if body.session_cookie is not None:
        config.SESSION_COOKIE = body.session_cookie
        settings["SESSION_COOKIE"] = body.session_cookie

    if body.model_id is not None:
        config.DEEPSEEK_MODEL_ID = body.model_id
        settings["DEEPSEEK_MODEL_ID"] = body.model_id

    if body.user_name is not None:
        config.USER_NAME = body.user_name
        settings["USER_NAME"] = body.user_name

    if body.user_email is not None:
        config.USER_EMAIL = body.user_email
        settings["USER_EMAIL"] = body.user_email

    if body.bcc_email is not None:
        config.BCC_EMAIL = body.bcc_email
        settings["BCC_EMAIL"] = body.bcc_email

    if body.default_pages is not None:
        config.DEFAULT_PAGES = body.default_pages
        settings["DEFAULT_PAGES"] = body.default_pages

    _save_settings(settings)
    return {"ok": True}


@router.post("/config/cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=422, detail="CV must be a .docx file")
    os.makedirs("data", exist_ok=True)
    with open(config.CV_FILE, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"ok": True, "path": config.CV_FILE}


@router.post("/config/datalake")
async def upload_datalake(file: UploadFile = File(...)):
    os.makedirs("data", exist_ok=True)
    with open(config.DATA_LAKE_FILE, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"ok": True, "path": config.DATA_LAKE_FILE}

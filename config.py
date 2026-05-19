# =============================================================================
# Auto-Apply Configuration
# All tuneable variables live here — edit this file to configure the system.
# Secrets (API keys) are loaded from .env — never commit .env to git.
# =============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

# --- Dashscope AI ---
DASHSCOPE_API_KEY: str = os.environ["DASHSCOPE_API_KEY"]
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_MODEL_ID = "qwen3.6-flash"
DASHSCOPE_THINKING = False  # Set True to enable chain-of-thought (slower)

# --- HKUST Job Board ---
HKUST_JOB_BOARD_URL = "https://career.hkust.edu.hk/web/job.php"
# Paste a fresh PHPSESSID cookie value here (grab from browser DevTools → Network)
SESSION_COOKIE = "YOUR_PHPSESSID_VALUE_HERE"
DEFAULT_PAGES = "1-3"  # Default page range shown at startup

# --- Scraper timing ---
REQUEST_TIMEOUT = 25       # seconds per HTTP request
SLEEP_BETWEEN_REQUESTS = 1.0  # seconds between detail-page fetches

# --- User identity (used in email body and document headers) ---
USER_NAME = "Your Full Name"
USER_EMAIL = "your@email.com"
BCC_EMAIL = ""  # Optional BCC address on outgoing emails (leave empty to disable)

# --- File paths ---
CV_FILE = "data/my_cv.docx"           # Your source CV (DOCX)
DATA_LAKE_FILE = "data/data_lake.md"  # Free-text file with extra personal info
STATE_FILE = "hkust_jobs.csv"         # Persistent job tracking CSV

# --- Output directories ---
OUTPUT_CV_DIR = "output/cv"
OUTPUT_LETTER_DIR = "output/cover_letters"

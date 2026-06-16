import os
import time

try:
    import pythoncom
    import win32com.client
    import pywintypes
    _OUTLOOK_AVAILABLE = True
except ImportError:
    _OUTLOOK_AVAILABLE = False

import config


def is_available() -> bool:
    return _OUTLOOK_AVAILABLE


def _dispatch_outlook(retries: int = 3, delay: float = 1.5):
    """Connect to a running Outlook instance, retrying on RPC_E_CALL_REJECTED."""
    last_err = None
    for attempt in range(retries):
        try:
            return win32com.client.Dispatch("outlook.application")
        except Exception as e:
            last_err = e
            err_str = str(e)
            # -2147418111 is RPC_E_CALL_REJECTED — Outlook is busy/starting up
            if "-2147418111" in err_str or "rejected" in err_str.lower():
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
            break
    raise RuntimeError(
        f"Could not connect to Outlook. Make sure Outlook is open and signed in. Detail: {last_err}"
    )


def _default_body(company: str, job_title: str) -> str:
    return (
        f"Dear {company} Recruitment Team,\n\n"
        f"I am writing to express my interest in the {job_title} role at {company}.\n\n"
        f"Please find attached my tailored CV and cover letter for your consideration.\n\n"
        f"I look forward to the opportunity to discuss how my experience and skills can "
        f"contribute to {company}.\n\n"
        f"Best Regards,\n{config.USER_NAME}"
    )


def send_application(
    to_email: str,
    job: dict,
    cv_path: str,
    letter_path: str,
    subject: str = "",
    body: str = "",
) -> tuple[bool, str]:
    """
    Send a job application email via Outlook COM.
    `subject` / `body` are the AI-personalised content; when empty, fall back to the
    static subject and boilerplate body.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    if not _OUTLOOK_AVAILABLE:
        return False, "pywin32 not installed — run: pip install pywin32"

    company = job.get("company", "the company")
    job_title = job.get("job_title", "the position")

    # COM must be initialised on the calling thread. FastAPI runs sync routes in a
    # worker thread, so this is required there (the CLI's main thread also benefits).
    pythoncom.CoInitialize()
    try:
        outlook = _dispatch_outlook()
        mail = outlook.CreateItem(0)

        mail.To = to_email
        mail.Subject = subject.strip() or f"Application for {job_title}"
        mail.BodyFormat = 1  # Plain text

        if config.BCC_EMAIL:
            mail.BCC = config.BCC_EMAIL

        mail.Body = body.strip() or _default_body(company, job_title)

        mail.Attachments.Add(os.path.abspath(cv_path))
        mail.Attachments.Add(os.path.abspath(letter_path))

        mail.Send()
        return True, ""

    except Exception as e:
        return False, str(e)
    finally:
        pythoncom.CoUninitialize()

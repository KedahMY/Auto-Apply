import os

try:
    import win32com.client
    _OUTLOOK_AVAILABLE = True
except ImportError:
    _OUTLOOK_AVAILABLE = False

import config


def is_available() -> bool:
    return _OUTLOOK_AVAILABLE


def send_application(
    to_email: str,
    job: dict,
    cv_path: str,
    letter_path: str,
) -> bool:
    """
    Send a job application email via Outlook COM.
    Returns True on success, False on failure.
    """
    if not _OUTLOOK_AVAILABLE:
        print("  ERROR: pywin32 / Outlook not available. Install pywin32.")
        return False

    company = job.get("company", "the company")
    job_title = job.get("job_title", "the position")

    try:
        outlook = win32com.client.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)

        mail.To = to_email
        mail.Subject = f"Application for {job_title}"
        mail.BodyFormat = 1  # Plain text

        if config.BCC_EMAIL:
            mail.BCC = config.BCC_EMAIL

        mail.Body = (
            f"Dear {company} Recruitment Team,\n\n"
            f"I am writing to express my interest in the {job_title} role at {company}.\n\n"
            f"Please find attached my tailored CV and cover letter for your consideration.\n\n"
            f"I look forward to the opportunity to discuss how my experience and skills can "
            f"contribute to {company}.\n\n"
            f"Best Regards,\n{config.USER_NAME}"
        )

        if os.path.exists(cv_path):
            mail.Attachments.Add(os.path.abspath(cv_path))
        else:
            print(f"  Warning: CV not found at {cv_path}")

        if os.path.exists(letter_path):
            mail.Attachments.Add(os.path.abspath(letter_path))
        else:
            print(f"  Warning: cover letter not found at {letter_path}")

        mail.Send()
        return True

    except Exception as e:
        print(f"  ERROR sending email: {e}")
        return False

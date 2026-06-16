import json
from openai import OpenAI
import config

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
    return _client


_SYSTEM_PROMPT = """You are an expert job-application assistant. Write the SUBJECT LINE and BODY \
of a short, personalised application email that a candidate sends to a company's recruitment team. \
The candidate's tailored CV and cover letter are attached as separate documents.

Rules:
- The email is a brief covering message — NOT a repeat of the cover letter. 120-160 words for the body.
- Reference the company name and job title naturally.
- Mention that the tailored CV and cover letter are attached for the recruiter's consideration.
- Pull one or two concrete, relevant strengths from the CV — do not fabricate anything.
- Warm, professional, confident tone. Plain text only (no markdown, no bullet symbols).
- The body MUST include the salutation "Dear {company} Recruitment Team," at the top and a \
sign-off "Best Regards,\\n{candidate name}" at the bottom.
- The subject should be concise and specific (e.g. reference the role); avoid generic spam-like phrasing.
- Return ONLY valid JSON with exactly two string keys: "subject" and "body". No markdown fences, \
no explanation, nothing else.
  Example: {"subject": "Application for Data Analyst — Jane Doe", "body": "Dear ... Best Regards,\\nJane Doe"}"""


def generate_email(cv_text: str, data_lake: str, job: dict) -> tuple[str, str]:
    """
    Return (subject, body) for a personalised application email.
    On any error or unparseable response, return ("", "") so the caller falls back
    to the static subject + boilerplate body.
    """
    user_prompt = (
        f"=== CANDIDATE NAME ===\n{config.USER_NAME}\n\n"
        f"=== MY CV ===\n{cv_text}\n\n"
        f"=== ADDITIONAL PERSONAL INFO ===\n{data_lake}\n\n"
        f"=== JOB POSTING ===\n"
        f"Company: {job.get('company', '')}\n"
        f"Role: {job.get('job_title', '')}\n"
        f"Nature: {job.get('job_nature', '')}\n"
        f"Description:\n{job.get('details', '')}\n\n"
        "Write the application email. Return the JSON object with 'subject' and 'body'."
    )

    try:
        response = _get_client().chat.completions.create(
            model=config.DEEPSEEK_MODEL_ID,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if the model wraps its output
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        subject = str(data.get("subject", "")).strip()
        body = str(data.get("body", "")).strip()
        return subject, body
    except Exception:
        return "", ""

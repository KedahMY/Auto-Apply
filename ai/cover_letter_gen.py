from openai import OpenAI
import config

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.DASHSCOPE_BASE_URL,
        )
    return _client


_SYSTEM_PROMPT = """You are an expert cover letter writer. Write a personalised, concise cover letter for a job application.

Rules:
- Address it to the company's recruitment team (do not write a salutation line — that is added separately).
- 3-4 paragraphs: (1) why this specific role, (2) relevant experience and achievements, (3) what you bring to the company, (4) closing call-to-action.
- Reference the company name and job title naturally.
- Draw on the candidate's CV and personal info to keep it authentic and specific.
- Professional but warm tone; avoid generic filler phrases.
- Output the body text only — no salutation ("Dear...") and no sign-off ("Best regards..."); those are added separately.
- Do NOT include any preamble or explanation."""


def generate_cover_letter(cv_text: str, data_lake: str, job: dict) -> str:
    """Return the body of a personalised cover letter as plain text."""
    user_prompt = (
        f"=== MY CV ===\n{cv_text}\n\n"
        f"=== ADDITIONAL PERSONAL INFO ===\n{data_lake}\n\n"
        f"=== JOB POSTING ===\n"
        f"Company: {job.get('company', '')}\n"
        f"Role: {job.get('job_title', '')}\n"
        f"Nature: {job.get('job_nature', '')}\n"
        f"Description:\n{job.get('details', '')}\n\n"
        "Please write a personalised cover letter body for this role."
    )

    response = _get_client().chat.completions.create(
        model=config.DASHSCOPE_MODEL_ID,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        extra_body={"enable_thinking": config.DASHSCOPE_THINKING},
    )
    return response.choices[0].message.content.strip()

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


_SYSTEM_PROMPT = """You are an expert CV writer and career coach. Your task is to rewrite a candidate's CV so it is tailored to a specific job posting, maximising relevance without fabricating any experience or skills.

Rules:
- Preserve ALL true information; do not invent anything.
- Reorder and emphasise bullet points that match the job requirements.
- Use keywords from the job description naturally.
- Keep the same section structure (e.g. Education, Experience, Skills, Projects).
- Output the tailored CV as plain text with section headings in ALL CAPS followed by a blank line, and bullet points starting with "- ".
- Do NOT include any preamble or explanation — output the CV text only."""


def tailor_cv(cv_text: str, data_lake: str, job: dict) -> str:
    """Return a tailored CV as structured plain text."""
    user_prompt = (
        f"=== MY CV ===\n{cv_text}\n\n"
        f"=== ADDITIONAL PERSONAL INFO ===\n{data_lake}\n\n"
        f"=== JOB POSTING ===\n"
        f"Company: {job.get('company', '')}\n"
        f"Role: {job.get('job_title', '')}\n"
        f"Nature: {job.get('job_nature', '')}\n"
        f"Description:\n{job.get('details', '')}\n\n"
        "Please rewrite my CV tailored to this role."
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

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


_SYSTEM_PROMPT = """You are an expert cover letter writer. Write a personalised, substantive cover letter for a job application.

Rules:
- Address it to the company's recruitment team (do not write a salutation line — that is added separately).
- 3 to 4 paragraphs: (1) why this specific role and company excites you, (2) your most relevant experience with concrete details, (3) what specific skills and qualities you bring, (4) closing call-to-action.
- Target 300–400 words total. This fits comfortably on one page with the surrounding header and sign-off.
- Be specific and concrete — name actual projects, tools, metrics, or achievements from the CV. Avoid generic filler.
- Reference the company name and job title naturally within the body.
- Professional but warm, confident tone.
- Do NOT use em dashes (—) or en dashes (–) anywhere. Use commas, periods, or rephrase the sentence instead.
- Output the body text only: no salutation ("Dear...") and no sign-off ("Best regards..."); those are added separately.
- Do NOT include any preamble or explanation."""


_MAX_WORDS = 300
_SHORTEN_SYSTEM = (
    "You are a cover letter editor. The cover letter body below exceeds the 300-word limit. "
    "Rewrite it to be under 300 words while keeping the core message, company name, job title, "
    "and the strongest achievements. Cut filler phrases aggressively. "
    "Do NOT use em dashes (—) or en dashes (–); use commas or periods instead. "
    "Output the body text only: no salutation, no sign-off, no explanation."
)


def _call_api(messages: list) -> str:
    response = _get_client().chat.completions.create(
        model=config.DEEPSEEK_MODEL_ID,
        messages=messages,
    )
    return response.choices[0].message.content.strip()


def generate_cover_letter(cv_text: str, data_lake: str, job: dict) -> str:
    """Return the body of a personalised cover letter, enforced to ≤300 words."""
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

    body = _call_api([
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    # Enforce word limit — retry up to 2 times if over limit
    for _ in range(2):
        word_count = len(body.split())
        if word_count <= _MAX_WORDS:
            break
        body = _call_api([
            {"role": "system", "content": _SHORTEN_SYSTEM},
            {"role": "user", "content": f"Current word count: {word_count}. Cover letter body to shorten:\n\n{body}"},
        ])

    return body

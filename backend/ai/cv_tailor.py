import json
from docx import Document
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


_SYSTEM_PROMPT = """You are an expert CV tailoring assistant.

You will receive a numbered list of every paragraph in a candidate's CV, then a job posting.
Your job: return a JSON object mapping paragraph indices (as strings) to rewritten text.

STRICT RULES:
1. Only rewrite bullet point paragraphs — lines that describe work experience, activities, or achievements.
2. Do NOT touch: name, contact info, section headings (e.g. EDUCATION, WORKING EXPERIENCE), company/role/date lines, or education entries.
3. Preserve ALL facts — do not fabricate anything.
4. Rewrite bullets to naturally incorporate keywords from the job posting. Reorder bullets within a role to put the most relevant first.
5. Keep each rewritten bullet the SAME length or SHORTER than the original — never longer. The CV must fit on a single page, so do not add length.
6. Output text only — no leading bullet characters (no •, -, –) since those are added by the document style.
7. Return ONLY valid JSON — no explanation, no markdown fences, nothing else.
   Example: {"12": "Rewritten text here.", "15": "Another rewritten bullet."}
8. If no changes are needed, return {}."""


def tailor_cv(cv_path: str, data_lake: str, job: dict) -> dict[str, str]:
    """
    Return a dict mapping paragraph index (str) → rewritten text for bullet paragraphs only.
    Caller applies these as surgical replacements to a copy of the original DOCX.
    """
    doc = Document(cv_path)

    lines = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        lines.append(f"{i}: {text}" if text else f"{i}: [empty line]")

    para_listing = "\n".join(lines)

    user_prompt = (
        f"=== CV PARAGRAPHS (index: text) ===\n{para_listing}\n\n"
        f"=== ADDITIONAL PERSONAL INFO ===\n{data_lake}\n\n"
        f"=== TARGET JOB ===\n"
        f"Company: {job.get('company', '')}\n"
        f"Role: {job.get('job_title', '')}\n"
        f"Nature: {job.get('job_nature', '')}\n"
        f"Description:\n{job.get('details', '')}\n\n"
        "Return the JSON object of paragraph replacements."
    )

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

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}

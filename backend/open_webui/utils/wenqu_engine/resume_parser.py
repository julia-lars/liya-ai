"""Resume parser — extract structured projects from PDF/text resumes."""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


RESUME_EXTRACTION_PROMPT = """You are analyzing a computer science student's resume for a graduate school interview (保研复试).

Extract the following structured information from the resume text:

1. **projects**: List each research/project experience with:
   - title: project name
   - description: brief summary (1-2 sentences)
   - tech_stack: list of technologies/models used
   - role: student's role in the project
   - duration: when it was done
   - highlights: key achievements or results

2. **publications**: List any papers with title, venue, year

3. **skills**: Technical skills listed

4. **competitions**: Any competition experience

Return the result as a JSON object.

Resume text:
{resume_text}
"""


async def parse_resume(resume_text: str, llm_callback) -> dict:
    """Parse resume text into structured project data using LLM.

    Args:
        resume_text: Raw text extracted from PDF
        llm_callback: Async function to call LLM with prompt -> response text

    Returns:
        dict with keys: projects, publications, skills, competitions
    """
    if not resume_text or not resume_text.strip():
        return {"projects": [], "publications": [], "skills": [], "competitions": []}

    prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text[:8000])

    try:
        response = await llm_callback(prompt)
        # Try to parse JSON from response
        parsed = _extract_json(response)
        if parsed:
            return parsed
    except Exception as e:
        log.error(f"Resume parsing failed: {e}")

    return {"projects": [], "publications": [], "skills": [], "competitions": []}


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    # Try direct parse
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try to find JSON block
    import re

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None

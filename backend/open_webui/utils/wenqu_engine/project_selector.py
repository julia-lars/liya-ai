"""Project selector — identify the most vulnerable research project for deep questioning."""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


PROJECT_SELECTION_PROMPT = """You are a professor evaluating candidates for graduate school admissions (保研复试).

Given these research projects from a student's resume, identify which ONE project is MOST likely to be deeply questioned by an interview committee.

Criteria for "high-risk" projects:
- The project makes strong claims but the student's described role seems shallow
- Complex technical terms are used but the description lacks depth
- The project touches on popular topics (LLM, diffusion models, etc.) where superficial knowledge is common
- The project description has inconsistencies or uses buzzwords without substance
- The methodology described seems incomplete or has obvious gaps

For each project, assign a "risk_score" (1-10) and explain why it's vulnerable.

Return JSON array:
[
  {{
    "title": "project name",
    "risk_score": 8,
    "reason": "why this project is risky"
  }},
  ...
]

Projects:
{projects_json}
"""


async def select_target_project(
    projects: list, llm_callback
) -> tuple[Optional[dict], list]:
    """Select the most vulnerable project for deep questioning.

    Args:
        projects: List of project dicts from resume parser
        llm_callback: Async function to call LLM

    Returns:
        (selected_project, all_scored_projects)
        selected_project is the highest-risk project dict
    """
    if not projects:
        return None, []

    if len(projects) == 1:
        return projects[0], projects

    prompt = PROJECT_SELECTION_PROMPT.format(projects_json=json.dumps(projects, ensure_ascii=False))

    try:
        response = await llm_callback(prompt)
        scored = _extract_json_array(response)
        if scored and len(scored) > 0:
            # Sort by risk_score descending
            scored.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
            top_title = scored[0]["title"]

            # Find matching project
            for proj in projects:
                if proj.get("title", "").lower() == top_title.lower():
                    return proj, scored

    except Exception as e:
        log.error(f"Project selection failed: {e}")

    # Fallback: return first project
    return projects[0], projects


def _extract_json_array(text: str) -> Optional[list]:
    """Extract JSON array from LLM response text."""
    text = text.strip()
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    import re

    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None

"""Project selector — identify the most vulnerable research project for deep questioning."""

import json
import logging
import re
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

For EACH project, assign a "risk_score" (1-10) and explain why it's vulnerable.

Return a JSON array with ALL projects, each scored:
[
  {{
    "title": "project name (must match exactly)",
    "risk_score": 1-10,
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
    """Score all projects and identify the most vulnerable one.

    Args:
        projects: List of project dicts from resume parser
        llm_callback: Async function to call LLM

    Returns:
        (selected_project, all_scored_projects)
        selected_project is the highest-risk project dict (with risk_score, reason)
        all_scored_projects is the full list sorted by risk_score descending
    """
    if not projects:
        return None, []

    if len(projects) == 1:
        # Single project — give it a default score
        scored = _with_default_score(projects[0])
        return scored, [scored]

    prompt = PROJECT_SELECTION_PROMPT.format(
        projects_json=json.dumps(projects, ensure_ascii=False)
    )

    try:
        response = await llm_callback(prompt)
        scored = _extract_json_array(response)

        if scored and len(scored) > 0:
            # Ensure all input projects have a score
            scored = _fill_missing_scores(projects, scored)

            # Sort by risk_score descending
            scored.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
            return scored[0], scored

    except Exception as e:
        log.error(f"Project selection failed: {e}")

    # Fallback: give all projects default scores
    all_scored = [_with_default_score(p) for p in projects]
    all_scored.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return all_scored[0], all_scored


def _with_default_score(project: dict) -> dict:
    """Add default risk_score and reason to a project dict."""
    return {
        "title": project.get("title", "未知项目"),
        "risk_score": 5,
        "reason": "未能完成AI评分，使用默认中等风险值",
    }


def _fill_missing_scores(projects: list, scored: list) -> list:
    """Fill in default scores for projects that the LLM didn't score.

    Matches by title (case-insensitive). Unmatched projects get a default score.
    """
    scored_by_title = {}
    for s in scored:
        title = s.get("title", "").strip().lower()
        if title:
            scored_by_title[title] = s

    result = []
    for p in projects:
        title = p.get("title", "").strip().lower()
        if title in scored_by_title:
            result.append(scored_by_title[title])
        else:
            log.warning(f"Project '{p.get('title')}' not scored by LLM, using default")
            result.append({
                "title": p.get("title", "未知项目"),
                "risk_score": 5,
                "reason": "AI未能对此项目进行评分",
            })

    return result


def _extract_json_array(text: str) -> Optional[list]:
    """Extract JSON array from LLM response text."""
    text = text.strip()

    # Try direct JSON parse first
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try finding JSON in code blocks — use greedy matching for the last bracket
    match = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Last resort: find first [ and last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None

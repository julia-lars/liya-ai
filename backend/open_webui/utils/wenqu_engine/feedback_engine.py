"""Feedback engine — generate comprehensive interview feedback reports."""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


FEEDBACK_PROMPT = """你是一位严格的计算机系博士生导师。请根据以下模拟面试的评估摘要，生成一份完整的反馈报告。

项目：{project_title}
项目描述：{project_description}

面试共 {total_rounds} 轮，每轮评估摘要：
{interview_log}

请从以下维度评估：

1. **学术深度** (Academic Depth, 1-10)
2. **表达清晰度** (Expression Clarity, 1-10)
3. **真实性风险** (Authenticity Risk, 1-10, 越高越可疑)
4. **漏洞分析** — 列出你从问答中发现的具体漏洞
5. **改进建议** — 针对每个漏洞给出可执行的改进方案

以JSON格式返回（不要包含无关内容，只返回JSON）：
{{
  "academic_score": 1-10,
  "expression_score": 1-10,
  "authenticity_score": 1-10,
  "risk_flags": ["漏洞1", "漏洞2"],
  "improvement_suggestions": ["建议1", "建议2"],
  "full_report": "完整的Markdown格式反馈报告文本"
}}
"""


async def generate_feedback(
    project_title: str,
    project_description: str,
    rounds: list,
    llm_callback,
) -> dict:
    """Generate a comprehensive feedback report for an interview session.

    Args:
        project_title: Name of the project discussed
        project_description: Description of the project
        rounds: List of dicts with question, answer, evaluation, depth_score
        llm_callback: Async function(prompt, system_prompt) -> response text

    Returns:
        dict with keys: academic_score, expression_score, authenticity_score,
                        risk_flags, improvement_suggestions, full_report
    """
    if not rounds:
        return _empty_report()

    interview_log = "\n".join(
        [
            f"第{r['round_number']}轮(类型:{r.get('question_type','?')},深度分:{r.get('depth_score','?')}) 评估: {r.get('evaluation', '')} 学生回答摘要: {(r.get('answer','') or '')[:200]}"
            for r in rounds
        ]
    )

    prompt = FEEDBACK_PROMPT.format(
        project_title=project_title,
        project_description=project_description[:1000],
        total_rounds=len(rounds),
        interview_log=interview_log,
    )

    try:
        response = await llm_callback(prompt)
        log.warning(f"Raw feedback response (first 500 chars): {response[:500]}")
        result = _extract_json(response)

        if result and "academic_score" in result:
            return result
        log.warning(f"Feedback JSON parse failed or missing academic_score. Raw response length: {len(response)}. Parsed result: {result}")
    except Exception as e:
        log.error(f"Feedback generation failed: {e}")

    return _empty_report()


def _empty_report(reason: str = "面试记录不足") -> dict:
    return {
        "academic_score": 0,
        "expression_score": 0,
        "authenticity_score": 0,
        "risk_flags": [f"无法生成评估——{reason}"],
        "improvement_suggestions": ["请完成至少一轮面试问答或检查模型API是否正常工作"],
        "full_report": f"无法生成完整反馈报告：{reason}。\n\n可能的原因为：API超时、模型返回格式异常、或面试记录不完整。",
    }


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    import re

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None

"""Feedback engine — generate comprehensive interview feedback reports."""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


FEEDBACK_PROMPT = """你是一位严格的计算机系博士生导师。请根据以下模拟面试记录，生成一份完整的反馈报告。

项目：{project_title}
项目描述：{project_description}

面试记录（共 {total_rounds} 轮）：
{interview_log}

请从以下维度评估：

1. **学术深度** (Academic Depth, 1-10)
   - 学生是否真正理解核心原理？
   - 是否能清晰解释技术选型理由？
   - 对Baseline和实验设计的理解程度？

2. **表达清晰度** (Expression Clarity, 1-10)
   - 回答是否结构清晰、逻辑自洽？
   - 学术用语是否规范？
   - 是否回避问题或答非所问？

3. **真实性风险** (Authenticity Risk, 1-10, 越高越可疑)
   - 是否存在夸大或编造成分？
   - 技术描述是否consistent？
   - 个人贡献的描述是否可信？

4. **漏洞分析** — 列出你在对话中发现的具体漏洞
5. **改进建议** — 针对每个漏洞给出可执行的改进方案

以JSON格式返回：
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

    interview_log = "\n\n".join(
        [
            f"第 {r['round_number']} 轮\n"
            f"导师问：{r.get('question', '')}\n"
            f"学生答：{r.get('answer', '（未回答）')}\n"
            f"评估：{r.get('evaluation', '')}"
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
        result = _extract_json(response)

        if result and "academic_score" in result:
            return result
    except Exception as e:
        log.error(f"Feedback generation failed: {e}")

    return _empty_report()


def _empty_report() -> dict:
    return {
        "academic_score": 0,
        "expression_score": 0,
        "authenticity_score": 0,
        "risk_flags": ["无法生成评估——面试记录不足"],
        "improvement_suggestions": ["请完成至少一轮面试问答"],
        "full_report": "面试记录不足，无法生成完整反馈报告。",
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

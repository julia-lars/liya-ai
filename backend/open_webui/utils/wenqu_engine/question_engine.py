"""Question engine — the core academic probing engine for multi-round interviews."""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一位极其严格的计算机系博士生导师，长期参与保研复试。

你会通过连续追问验证学生科研经历的真实性。

重点考察：
- 原理理解
- 实验设计
- 技术选型
- Baseline
- Failure Analysis
- 改进能力
- 学术表达严谨度

禁止泛泛鼓励，必须持续施压。"""


INITIAL_QUESTION_PROMPT = """学生的科研项目如下：

项目名称：{project_title}
项目描述：{project_description}

这是第一轮追问。请对这个项目提出一个尖锐的、需要深入思考的问题。
聚焦在技术细节、模型选型、或实验设计上。不要问泛泛的问题。

问题必须能检验学生是否真正理解这个项目的核心工作。

请以JSON格式返回：
{{
  "question": "你的问题",
  "question_type": "principle|experiment|tech_choice|baseline|failure_case",
  "expected_depth": "考察的具体能力"
}}"""


FOLLOW_UP_PROMPT = """你正在对一名保研复试学生进行连续追问。

项目：{project_title}
项目描述：{project_description}

对话历史：
{chat_history}

这是第 {round_number} 轮追问。根据学生上一轮的回答，继续深挖。

要求：
1. 如果学生回答含糊，追问具体技术细节
2. 如果学生回答正确，进入更深一层（如：你的Baseline是什么？为什么选这个而不是那个？）
3. 如果学生暴露了知识盲区，在这个点上持续施压
4. 每轮只问1个问题，但要尖锐

请以JSON格式返回：
{{
  "question": "你的问题",
  "question_type": "principle|experiment|tech_choice|baseline|failure_case|improvement",
  "evaluation": "对学生上一轮回答的简短评估（考察点、漏洞、或亮点）",
  "depth_score": 1-10
}}"""


async def generate_first_question(
    project_title: str, project_description: str, llm_callback
) -> dict:
    """Generate the first probing question for a project.

    Args:
        project_title: Name of the selected project
        project_description: Description of the project
        llm_callback: Async function(prompt, system_prompt) -> response text

    Returns:
        dict with keys: question, question_type, expected_depth
    """
    prompt = INITIAL_QUESTION_PROMPT.format(
        project_title=project_title,
        project_description=project_description[:2000],
    )

    response = await llm_callback(prompt, system_prompt=SYSTEM_PROMPT)
    result = _extract_json(response)

    if result and "question" in result:
        return result

    # Fallback
    return {
        "question": f"请详细解释一下你在{project_title}中使用的核心方法，以及为什么选择这种方法而不是其他方案？",
        "question_type": "principle",
        "expected_depth": "原理理解与技术选型判断",
    }


async def generate_follow_up_question(
    project_title: str,
    project_description: str,
    chat_history: list,
    round_number: int,
    llm_callback,
) -> dict:
    """Generate a follow-up question based on conversation history.

    Args:
        project_title: Name of the selected project
        project_description: Description of the project
        chat_history: List of {"question": str, "answer": str} dicts
        round_number: Current round number (1-indexed)
        llm_callback: Async function(prompt, system_prompt) -> response text

    Returns:
        dict with keys: question, question_type, evaluation, depth_score
    """
    history_text = "\n".join(
        [
            f"导师：{r['question']}\n学生：{r.get('answer', '（未回答）')}"
            for r in chat_history
        ]
    )

    prompt = FOLLOW_UP_PROMPT.format(
        project_title=project_title,
        project_description=project_description[:1000],
        chat_history=history_text,
        round_number=round_number,
    )

    response = await llm_callback(prompt, system_prompt=SYSTEM_PROMPT)
    result = _extract_json(response)

    if result and "question" in result:
        return result

    # Fallback
    return {
        "question": "你能更具体地解释一下你在这个项目中的个人贡献吗？哪些部分是你独立完成的？",
        "question_type": "principle",
        "evaluation": "",
        "depth_score": 5,
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

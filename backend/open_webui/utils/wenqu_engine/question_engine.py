"""Question engine — the core academic probing engine for multi-round interviews.

Question progression: 由浅入深，由宏观到微观
  Round 1: 宏观原理 (principle)
  Round 2: 技术选型 (tech_choice)
  Round 3: 实验细节/设计 (experiment)
  Round 4: Failure case / 瓶颈分析 (failure_case)
  Round 5: 改进方向 / Ablation (improvement)

If the student is stuck on the current direction, the engine automatically
switches to a different angle to keep the interview productive.
"""

import json
import logging
import re
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


# General guideline — not a rigid schedule
PROGRESSION_GUIDE = """
面试的整体节奏建议由宏观到微观、由浅入深，但不要机械地按固定顺序走。

请根据学生上一轮的回答灵活判断：
- 如果学生回答有深度、有细节 → 可以继续深挖同一个方向，追问更具体的细节
- 如果学生回答含糊、表面化 → 换一个角度考察，看看是不是只是在背概念
- 如果学生答不出来 → 果断切换方向，不要死磕
- 尽量覆盖多个维度：原理理解、技术选型、实验设计、Baseline、Failure analysis、改进方向
"""


STUCK_KEYWORDS = [
    "不知道", "不确定", "没想过", "不太清楚", "不了解", "不熟悉",
    "没有考虑", "没有研究", "没有对比", "不记得", "忘了",
    "不太确定", "说不清楚", "很难说", "不好说", "忘了",
    "这个嘛", "嗯...", "那个...", "可能吧", "大概是",
    "不是我做的", "我负责的部分是", "我只做了",
    "我也不太清楚", "没有深入了解",
]


def is_stuck(answer: str) -> tuple[bool, str]:
    """Detect if the student's answer indicates they are stuck.

    Returns:
        (is_stuck: bool, reason: str)
    """
    if not answer or len(answer.strip()) < 15:
        return True, "回答过短（少于15个字符），缺乏实质内容"

    answer_lower = answer.lower()
    for kw in STUCK_KEYWORDS:
        if kw in answer_lower:
            return True, f"检测到回避性表达「{kw}」，可能对此方向不了解"

    return False, ""


INITIAL_QUESTION_PROMPT = """学生的科研项目如下：

项目名称：{project_title}
项目描述：{project_description}

这是第一轮追问。请从这个项目的核心原理出发，提出一个宏观层面的问题，考察学生是否真正理解项目涉及的核心概念。

问题必须能检验学生是否真正理解这个项目的核心工作，不要问浮于表面的问题。

请以JSON格式返回：
{{
  "question": "你的问题（只问一个问题，不要包含多个子问题，不要用'和'/'以及'连接多个问题）",
  "question_type": "principle|tech_choice|experiment|baseline|failure_case|improvement",
  "expected_depth": "考察的具体能力"
}}"""


FOLLOW_UP_PROMPT = """你正在对一名保研复试学生进行连续追问。

项目：{project_title}
项目描述：{project_description}

对话历史：
{chat_history}

这是第 {round_number} 轮追问。

{progression_guide}

{stuck_hint}

请以JSON格式返回：
{{
  "question": "你的问题（⚠️只问一个问题，不能同时问多个！不要用'和'、'以及'、'或'连接不同的问题）",
  "question_type": "principle|tech_choice|experiment|baseline|failure_case|improvement",
  "evaluation": "对学生上一轮回答的简短评估（考察点、漏洞、或亮点）",
  "depth_score": 1-10
}}"""


def _build_chat_history_text(chat_history: list) -> str:
    """Format chat history for prompt insertion."""
    lines = []
    for i, r in enumerate(chat_history, 1):
        answer = r.get("answer", "").strip() or "（未回答）"
        lines.append(f"第{i}轮\n导师：{r['question']}\n学生：{answer}")
    return "\n\n".join(lines)

async def generate_first_question(
    project_title: str, project_description: str, llm_callback
) -> dict:
    """Generate the first probing question — starting from core principles."""
    prompt = INITIAL_QUESTION_PROMPT.format(
        project_title=project_title,
        project_description=project_description[:2000],
    )

    response = await llm_callback(prompt, system_prompt=SYSTEM_PROMPT)
    result = _extract_json(response)

    if result and "question" in result:
        return _ensure_single_question(result)

    return {
        "question": f"请详细解释一下你在{project_title}中使用的核心方法？",
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
    """Generate a follow-up question with flexible direction switching.

    Checks if the student is stuck and switches direction if so.
    Otherwise lets the LLM decide whether to dive deeper or change angle.
    """
    history_text = _build_chat_history_text(chat_history)

    # Check if the last answer suggests the student is stuck
    stuck_hint = ""
    if chat_history:
        last_answer = chat_history[-1].get("answer", "")
        stuck, reason = is_stuck(last_answer)
        if stuck:
            stuck_hint = (
                f"【注意】学生上一轮的回答显示他可能在此方向上遇到了瓶颈"
                f"（{reason}）。请切换到一个不同的角度提问，"
                f"不要继续追问上一个问题。"
            )
            log.info(f"Round {round_number}: Student stuck — {reason}. Switching direction.")

    prompt = FOLLOW_UP_PROMPT.format(
        project_title=project_title,
        project_description=project_description[:1000],
        chat_history=history_text,
        round_number=round_number,
        progression_guide=PROGRESSION_GUIDE,
        stuck_hint=stuck_hint,
    )

    response = await llm_callback(prompt, system_prompt=SYSTEM_PROMPT)
    result = _extract_json(response)

    if result and "question" in result:
        return _ensure_single_question(result)

    return {
        "question": "你能更具体地解释一下你在这个项目中的个人贡献吗？",
        "question_type": "principle",
        "evaluation": "",
        "depth_score": 5,
    }


def _ensure_single_question(result: dict) -> dict:
    """Post-process to ensure only one question is asked per round.

    If the LLM returns multiple questions (e.g. "你的方法是什么？为什么选这个？"),
    split by question marks and keep only the first question.
    """
    question = result.get("question", "")
    if not question:
        return result

    # Split by Chinese/English question marks
    import re

    parts = re.split(r"[？?]", question)
    if len(parts) > 2:
        # More than one question — keep only the first
        first_question = parts[0].strip() + "？"
        log.info(
            f"Truncated multi-question response ({len(parts)-1} questions): "
            f"'{question[:60]}...' -> '{first_question[:60]}...'"
        )
        result["question"] = first_question
    elif len(parts) == 2 and len(parts[1].strip()) > 0:
        # Two questions — check if the second is substantial
        first_part = parts[0].strip()
        second_part = parts[1].strip()
        # If second part is short (follow-up like "对吗？"), keep both
        if len(second_part) > 5:
            first_question = first_part + "？"
            log.info(
                f"Truncated dual-question: '{first_part}？{second_part}' -> '{first_question}'"
            )
            result["question"] = first_question

    return result


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None

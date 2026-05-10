"""Wenqu API Router — Academic Interview (保研复试模拟面试).

This module is original code added to the liya-ai (Open WebUI fork).
It provides endpoints for the complete interview flow:
  upload → parse → select → question → answer → feedback
"""

import json
import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from open_webui.utils.auth import get_verified_user
from open_webui.models.users import Users

from open_webui.models.wenqu import (
    WenquSessionForm,
    WenquSessionModel,
    WenquSessionTable,
    WenquAnswerForm,
    WenquRoundModel,
    WenquRoundTable,
    WenquFeedbackReportModel,
    WenquFeedbackReportTable,
)

from open_webui.utils.wenqu_engine.resume_parser import parse_resume
from open_webui.utils.wenqu_engine.project_selector import select_target_project
from open_webui.utils.wenqu_engine.question_engine import (
    generate_first_question,
    generate_follow_up_question,
)
from open_webui.utils.wenqu_engine.feedback_engine import generate_feedback

log = logging.getLogger(__name__)

router = APIRouter()

# Maximum interview rounds
MAX_ROUNDS = 5

# Placeholder for LLM call — will be wired to Open WebUI's model system
async def _default_llm(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Default LLM stub. Replace with actual Open WebUI model call."""
    log.warning("Using stub LLM — wire to actual model inference for production use")
    return '{"question": "请详细解释你的核心方法？", "question_type": "principle", "evaluation": "", "depth_score": 5}'


# Global config: set this to a real LLM caller during app init
wenqu_llm_callback = _default_llm


def set_llm_callback(callback):
    """Set the LLM callback used by Wenqu engine."""
    global wenqu_llm_callback
    wenqu_llm_callback = callback


############################
# Resume & Project
############################


class ResumeUploadResponse(BaseModel):
    projects: list
    publications: list
    skills: list
    competitions: list


@router.post("/parse-resume", response_model=ResumeUploadResponse)
async def api_parse_resume(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
):
    """Parse resume text and extract structured project data."""
    resume_text = form_data.get("resume_text", "")
    if not resume_text:
        raise HTTPException(status_code=400, detail="resume_text is required")

    parsed = await parse_resume(resume_text, wenqu_llm_callback)
    return ResumeUploadResponse(**parsed)


class ProjectSelectResponse(BaseModel):
    selected_project: dict
    all_scored: list


@router.post("/select-project", response_model=ProjectSelectResponse)
async def api_select_project(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
):
    """Select the most vulnerable project for deep questioning."""
    projects = form_data.get("projects", [])
    if not projects:
        raise HTTPException(status_code=400, detail="projects list is required")

    selected, scored = await select_target_project(projects, wenqu_llm_callback)
    return ProjectSelectResponse(
        selected_project=selected or {},
        all_scored=scored,
    )


############################
# Session Management
############################


class CreateSessionResponse(BaseModel):
    session: WenquSessionModel


@router.post("/sessions", response_model=CreateSessionResponse)
async def api_create_session(
    request: Request,
    form_data: WenquSessionForm,
    user=Depends(get_verified_user),
):
    """Create a new interview session."""
    now = int(time.time())
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "resume_text": form_data.resume_text or "",
        "project_title": form_data.project_title or "",
        "project_description": form_data.project_description or "",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    session = await WenquSessionTable.insert_new(session_data)
    return CreateSessionResponse(session=session)


@router.get("/sessions", response_model=list[WenquSessionModel])
async def api_get_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    user=Depends(get_verified_user),
):
    """Get all interview sessions for the current user."""
    sessions = await WenquSessionTable.get_by_user_id(user.id, skip=skip, limit=limit)
    return sessions


@router.get("/sessions/{session_id}", response_model=WenquSessionModel)
async def api_get_session(
    session_id: str,
    user=Depends(get_verified_user),
):
    """Get a specific interview session."""
    session = await WenquSessionTable.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


############################
# Interview Rounds
############################


class NewRoundResponse(BaseModel):
    round: WenquRoundModel
    round_number: int


@router.post("/sessions/{session_id}/start")
async def api_start_interview(
    session_id: str,
    user=Depends(get_verified_user),
):
    """Start the interview — generate the first question."""
    session = await WenquSessionTable.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    first = await generate_first_question(
        session.project_title or "",
        session.project_description or "",
        wenqu_llm_callback,
    )

    now = int(time.time())
    round_data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "round_number": 1,
        "question": first.get("question", ""),
        "question_type": first.get("question_type", "principle"),
        "answer": None,
        "evaluation": first.get("expected_depth", ""),
        "depth_score": None,
        "created_at": now,
        "updated_at": now,
    }

    round_model = await WenquRoundTable.insert_new(round_data)
    await WenquSessionTable.update_status(session_id, "active")

    return {
        "round": WenquRoundModel.model_validate(round_model),
        "round_number": 1,
    }


@router.post("/sessions/{session_id}/answer")
async def api_submit_answer(
    session_id: str,
    form_data: WenquAnswerForm,
    user=Depends(get_verified_user),
):
    """Submit an answer to the current question, then get the next question if applicable."""
    session = await WenquSessionTable.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rounds = await WenquRoundTable.get_by_session(session_id)
    if not rounds:
        raise HTTPException(status_code=400, detail="No active round found")

    current_round = rounds[-1]

    # Update current round with answer
    await WenquRoundTable.update_answer(current_round.id, form_data.answer)

    # Refresh with updated data
    rounds = await WenquRoundTable.get_by_session(session_id)
    current_round = rounds[-1]

    next_round_number = len(rounds) + 1
    is_last_round = next_round_number > MAX_ROUNDS

    if is_last_round:
        # No more questions — wrap up
        await WenquSessionTable.update_status(session_id, "completed")
        return {
            "round": WenquRoundModel.model_validate(current_round),
            "next_question": None,
            "interview_complete": True,
        }

    # Generate follow-up question
    chat_history = [
        {"question": r.question, "answer": r.answer or ""} for r in rounds
    ]

    follow_up = await generate_follow_up_question(
        session.project_title or "",
        session.project_description or "",
        chat_history,
        next_round_number,
        wenqu_llm_callback,
    )

    # Insert next round
    now = int(time.time())
    next_round_data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "round_number": next_round_number,
        "question": follow_up.get("question", ""),
        "question_type": follow_up.get("question_type", "principle"),
        "answer": None,
        "evaluation": follow_up.get("evaluation", ""),
        "depth_score": follow_up.get("depth_score"),
        "created_at": now,
        "updated_at": now,
    }

    next_round = await WenquRoundTable.insert_new(next_round_data)

    # Update current round evaluation
    if follow_up.get("evaluation"):
        await WenquRoundTable.update_evaluation(
            current_round.id,
            follow_up.get("evaluation", ""),
            follow_up.get("depth_score", 5),
        )

    return {
        "round": WenquRoundModel.model_validate(next_round),
        "next_question": next_round.question,
        "interview_complete": False,
    }


@router.get("/sessions/{session_id}/rounds")
async def api_get_rounds(
    session_id: str,
    user=Depends(get_verified_user),
):
    """Get all rounds for a session."""
    rounds = await WenquRoundTable.get_by_session(session_id)
    return [WenquRoundModel.model_validate(r) for r in rounds]


############################
# Feedback Report
############################


@router.post("/sessions/{session_id}/feedback")
async def api_generate_feedback(
    session_id: str,
    user=Depends(get_verified_user),
):
    """Generate feedback report for a completed interview session."""
    session = await WenquSessionTable.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rounds = await WenquRoundTable.get_by_session(session_id)
    if not rounds:
        raise HTTPException(status_code=400, detail="No interview rounds found")

    # Check if report already exists
    existing = await WenquFeedbackReportTable.get_by_session(session_id)
    if existing:
        return {"report": WenquFeedbackReportModel.model_validate(existing)}

    # Prepare round data for feedback generation
    round_data = [
        {
            "round_number": r.round_number,
            "question": r.question or "",
            "answer": r.answer or "",
            "evaluation": r.evaluation or "",
            "depth_score": r.depth_score or 0,
        }
        for r in rounds
    ]

    feedback = await generate_feedback(
        session.project_title or "",
        session.project_description or "",
        round_data,
        wenqu_llm_callback,
    )

    now = int(time.time())
    report_data = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": user.id,
        "academic_score": feedback.get("academic_score", 0),
        "expression_score": feedback.get("expression_score", 0),
        "authenticity_score": feedback.get("authenticity_score", 0),
        "risk_flags": feedback.get("risk_flags", []),
        "improvement_suggestions": feedback.get("improvement_suggestions", []),
        "full_report": feedback.get("full_report", ""),
        "created_at": now,
    }

    report = await WenquFeedbackReportTable.insert_new(report_data)
    return {"report": WenquFeedbackReportModel.model_validate(report)}

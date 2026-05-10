import logging
import time
import uuid
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from open_webui.internal.db import Base, JSONField, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, String, Text, JSON

log = logging.getLogger(__name__)


####################
# Wenqu Session
# 问渠面试会话：一次完整的模拟面试
####################


class WenquSession(Base):
    __tablename__ = "wenqu_session"

    id = Column(String, primary_key=True, unique=True)
    user_id = Column(String, nullable=False)

    project_title = Column(Text, nullable=True)
    project_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)

    status = Column(String, default="pending")  # pending, active, completed

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class WenquSessionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    project_title: Optional[str] = None
    project_description: Optional[str] = None
    resume_text: Optional[str] = None

    status: str = "pending"

    created_at: int
    updated_at: int


class WenquSessionForm(BaseModel):
    resume_text: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None


####################
# Wenqu Round
# 单轮问答：一个追问 + 一个回答 + 评估
####################


class WenquRound(Base):
    __tablename__ = "wenqu_round"

    id = Column(String, primary_key=True, unique=True)
    session_id = Column(String, nullable=False)

    round_number = Column(BigInteger, nullable=False)

    question = Column(Text, nullable=True)
    question_type = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)

    evaluation = Column(Text, nullable=True)
    depth_score = Column(BigInteger, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class WenquRoundModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str

    round_number: int

    question: Optional[str] = None
    question_type: Optional[str] = None
    answer: Optional[str] = None

    evaluation: Optional[str] = None
    depth_score: Optional[int] = None

    created_at: int
    updated_at: int


class WenquAnswerForm(BaseModel):
    answer: str


####################
# Wenqu Feedback Report
# 面试结束后的综合反馈报告
####################


class WenquFeedbackReport(Base):
    __tablename__ = "wenqu_feedback_report"

    id = Column(String, primary_key=True, unique=True)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)

    academic_score = Column(BigInteger, nullable=True)
    expression_score = Column(BigInteger, nullable=True)
    authenticity_score = Column(BigInteger, nullable=True)

    risk_flags = Column(JSON, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)
    full_report = Column(Text, nullable=True)

    created_at = Column(BigInteger)


class WenquFeedbackReportModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    user_id: str

    academic_score: Optional[int] = None
    expression_score: Optional[int] = None
    authenticity_score: Optional[int] = None

    risk_flags: Optional[list] = None
    improvement_suggestions: Optional[list] = None
    full_report: Optional[str] = None

    created_at: int


####################
# DB Operations
####################


class WenquSessionTable:
    """CRUD operations for WenquSession."""

    @staticmethod
    async def insert_new(session_data: dict) -> WenquSessionModel:
        async with get_async_db_context() as db:
            session = WenquSession(**session_data)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return WenquSessionModel.model_validate(session)

    @staticmethod
    async def get_by_id(session_id: str) -> Optional[WenquSessionModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquSession).where(WenquSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                return WenquSessionModel.model_validate(session)
            return None

    @staticmethod
    async def get_by_user_id(
        user_id: str, skip: int = 0, limit: int = 50
    ) -> list[WenquSessionModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquSession)
                .where(WenquSession.user_id == user_id)
                .order_by(WenquSession.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return [
                WenquSessionModel.model_validate(session) for session in result.scalars()
            ]

    @staticmethod
    async def update_status(session_id: str, status: str) -> Optional[WenquSessionModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquSession).where(WenquSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = status
                session.updated_at = int(time.time())
                await db.commit()
                await db.refresh(session)
                return WenquSessionModel.model_validate(session)
            return None


class WenquRoundTable:
    """CRUD operations for WenquRound."""

    @staticmethod
    async def insert_new(round_data: dict) -> WenquRoundModel:
        async with get_async_db_context() as db:
            round_ = WenquRound(**round_data)
            db.add(round_)
            await db.commit()
            await db.refresh(round_)
            return WenquRoundModel.model_validate(round_)

    @staticmethod
    async def get_by_session(
        session_id: str, order: str = "asc"
    ) -> list[WenquRoundModel]:
        async with get_async_db_context() as db:
            query = select(WenquRound).where(WenquRound.session_id == session_id)
            if order == "asc":
                query = query.order_by(WenquRound.round_number.asc())
            else:
                query = query.order_by(WenquRound.round_number.desc())
            result = await db.execute(query)
            return [
                WenquRoundModel.model_validate(round_) for round_ in result.scalars()
            ]

    @staticmethod
    async def update_answer(
        round_id: str, answer: str
    ) -> Optional[WenquRoundModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquRound).where(WenquRound.id == round_id)
            )
            round_ = result.scalar_one_or_none()
            if round_:
                round_.answer = answer
                round_.updated_at = int(time.time())
                await db.commit()
                await db.refresh(round_)
                return WenquRoundModel.model_validate(round_)
            return None

    @staticmethod
    async def update_evaluation(
        round_id: str, evaluation: str, depth_score: int
    ) -> Optional[WenquRoundModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquRound).where(WenquRound.id == round_id)
            )
            round_ = result.scalar_one_or_none()
            if round_:
                round_.evaluation = evaluation
                round_.depth_score = depth_score
                round_.updated_at = int(time.time())
                await db.commit()
                await db.refresh(round_)
                return WenquRoundModel.model_validate(round_)
            return None


class WenquFeedbackReportTable:
    """CRUD operations for WenquFeedbackReport."""

    @staticmethod
    async def insert_new(report_data: dict) -> WenquFeedbackReportModel:
        async with get_async_db_context() as db:
            report = WenquFeedbackReport(**report_data)
            db.add(report)
            await db.commit()
            await db.refresh(report)
            return WenquFeedbackReportModel.model_validate(report)

    @staticmethod
    async def get_by_session(
        session_id: str,
    ) -> Optional[WenquFeedbackReportModel]:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(WenquFeedbackReport).where(
                    WenquFeedbackReport.session_id == session_id
                )
            )
            report = result.scalar_one_or_none()
            if report:
                return WenquFeedbackReportModel.model_validate(report)
            return None

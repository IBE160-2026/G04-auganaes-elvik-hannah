"""«?» on a Task (Story 5.1, FR-14, AD-4): POST /homes/{home_id}/tasks/{task_id}/answer.

Behind require_role like every route with {home_id}: any Member may ask, a Tenant too. The route
only translates; the limit, the provider and the failure rules live in app/ai and domain/ai_usage.
A refused call is 429 with when the count restarts, never a 200 with a made-up status.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import ai
from app.clock import UtcDatetime
from app.domain import tasks
from app.routes.deps import TASK_NOT_FOUND, AnyMember, ErrorOut, SessionDep

router = APIRouter(tags=["ai"])

LIMIT_REACHED = f"Du har brukt de {ai.service.AI_DAILY_LIMIT} KI-spørsmålene dine i dag."


class AskRequest(BaseModel):
    # Blank or missing: the service asks its default question.
    question: str | None = Field(default=None, max_length=ai.service.QUESTION_MAX_LENGTH)


class AnswerOut(BaseModel):
    status: Literal["ok", "low_confidence", "error"]
    answer: str
    # Its own field on every answer, never part of `answer` (AD-4).
    disclaimer: str
    # True when the mock provider answered (no GEMINI_API_KEY), so the UI can say so.
    demo: bool


class LimitOut(BaseModel):
    detail: str
    resets_at: UtcDatetime


@router.post(
    "/homes/{home_id}/tasks/{task_id}/answer",
    response_model=AnswerOut,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Member of this Home, or no such Home",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "No such Task in this Home"},
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": LimitOut,
            "description": "The user has used today's AI calls; resets_at says when they restart",
        },
    },
)
def ask_about_task(
    task_id: uuid.UUID, body: AskRequest, member: AnyMember, session: SessionDep
) -> Response | AnswerOut:
    try:
        task = tasks.active_task(session, member.home_id, task_id)
    except tasks.TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND) from None
    try:
        result = ai.answer_question(
            session, member.user_id, task.name, task.task_type, body.question
        )
    except ai.LimitReached as limit:
        out = LimitOut(detail=LIMIT_REACHED, resets_at=limit.resets_at)
        return JSONResponse(
            out.model_dump(mode="json"), status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    return AnswerOut(
        status=result.status, answer=result.answer, disclaimer=result.disclaimer, demo=result.demo
    )

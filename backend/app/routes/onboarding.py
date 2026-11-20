"""The onboarding guide of a Landlord Home (Story 5.3, FR-16, AD-4).

Home-scoped, so every route goes through require_role. The guide's Home-specific part (name and
current Must tasks) is read live; the introduction was stored when the Tasks were set up. Reading
never calls the AI.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app import ai
from app.domain import onboarding
from app.routes.deps import ErrorOut, GuideViewer, SessionDep, Tenant

router = APIRouter(prefix="/homes", tags=["onboarding"])

NO_GUIDE_YET = "Hjemmet har ingen oppgaver ennå, så det finnes ingen guide."


class GuideTaskOut(BaseModel):
    name: str
    frequency_days: int


class GuideOut(BaseModel):
    home_name: str
    intro: str
    source: Literal["ai", "demo", "fallback"]
    # The Must tasks as they are now, in the server's order.
    must_tasks: list[GuideTaskOut]
    # Whether this Member has dismissed the card.
    dismissed: bool
    # The AI disclaimer in its own field (AD-4); null for the fixed text we wrote ourselves.
    disclaimer: str | None
    # True when the mock wrote the introduction (no GEMINI_API_KEY).
    demo: bool


@router.get(
    "/{home_id}/onboarding-guide",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Tenant or the Landlord of this Home, or no such Home",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut, "description": "The Home has no Tasks yet"},
    },
)
def get_guide(member: GuideViewer, session: SessionDep) -> GuideOut:
    try:
        view = onboarding.guide_for(session, member)
    except onboarding.GuideNotAvailable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=NO_GUIDE_YET) from None
    written_by_ai = view.source in ("ai", "demo")
    return GuideOut(
        home_name=view.home_name,
        intro=view.intro,
        source=view.source,  # type: ignore[arg-type]
        must_tasks=[
            GuideTaskOut(name=t.name, frequency_days=t.frequency_days) for t in view.must_tasks
        ],
        dismissed=view.dismissed,
        disclaimer=ai.DISCLAIMER if written_by_ai else None,
        demo=view.source == "demo",
    )


@router.post(
    "/{home_id}/onboarding-guide/dismiss",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Not a Tenant of this Home, or no such Home",
        },
    },
)
def dismiss_guide(member: Tenant, session: SessionDep) -> Response:
    onboarding.dismiss(session, member)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

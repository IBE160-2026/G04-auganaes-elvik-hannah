"""The Landlord Portfolio (Story 6.1, FR-20).

User-scoped, like GET /homes: there is no home_id in the path, and portfolio_of filters on the
caller's own Landlord Memberships. Fewer than portfolio.MIN_HOMES of them is the same 403 the
frontend's global handler already reacts to, so a Landlord who loses a Home is sent home.
"""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.clock import utc_today
from app.domain import portfolio
from app.permissions.current_user import CurrentUser
from app.routes.deps import ErrorOut, SessionDep

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class OverdueTaskOut(BaseModel):
    task_id: uuid.UUID
    name: str
    due_on: date
    days_overdue: int


class PortfolioHomeOut(BaseModel):
    home_id: uuid.UUID
    name: str
    status: portfolio.PortfolioStatus
    overdue_tasks: list[OverdueTaskOut]
    due_soon_count: int


class PortfolioOut(BaseModel):
    # Behind first, then by name.
    homes: list[PortfolioHomeOut]


@router.get(
    "",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorOut,
            "description": "Landlord in fewer than two Homes",
        }
    },
)
def get_portfolio(user: CurrentUser, session: SessionDep) -> PortfolioOut:
    try:
        rows = portfolio.portfolio_of(session, user, utc_today())
    except portfolio.NotInPortfolio:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=portfolio.NOT_IN_PORTFOLIO) from None
    return PortfolioOut(
        homes=[
            PortfolioHomeOut(
                home_id=row.home.id,
                name=row.home.name,
                status=row.status,
                overdue_tasks=[OverdueTaskOut(**t._asdict()) for t in row.overdue],
                due_soon_count=row.due_soon_count,
            )
            for row in rows
        ]
    )

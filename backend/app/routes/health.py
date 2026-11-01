import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_engine

router = APIRouter()
logger = logging.getLogger(__name__)


def app_engine(request: Request) -> Engine:
    return get_engine(request.app.state.settings.database_url)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def health_db(engine: Annotated[Engine, Depends(app_engine)]) -> dict[str, str]:
    """Story 1.7: proves the deployed API reaches its database. Reveals only up or down."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Databasesjekk feilet")
        raise HTTPException(status_code=503, detail="Databasen svarer ikke") from None
    return {"database": "ok"}

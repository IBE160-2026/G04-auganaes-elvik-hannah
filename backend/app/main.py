"""FastAPI entry point. Routes are mounted under /api.

Frontend and API share one origin (AD-7): Vercel rewrites /api/* to this service with the
full path, and the Vite dev/preview servers proxy /api locally. So there is no CORS setup.
"""

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.routes import auth, health, homes


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Husly API")
    app.state.settings = settings
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(homes.router, prefix="/api")
    return app


app = create_app()

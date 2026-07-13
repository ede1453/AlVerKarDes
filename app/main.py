from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.observability import ObservabilityMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, version="0.6.0")

    app.add_middleware(ObservabilityMiddleware)

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

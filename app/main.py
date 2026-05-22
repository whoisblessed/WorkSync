from fastapi import FastAPI

from app.core.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        summary="Я люблю репера блейди у него довольно прикольные треки",
        version="1.0.0",
    )

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "Ок"}

    return app


app = create_app()

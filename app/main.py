from fastapi import FastAPI

from app.core.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        summary=f"ANIME{''.join([str(i) for i in range(1, 68)])}",
        version="1.4.8.8",
    )

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "Ок"}

    return app


app = create_app()

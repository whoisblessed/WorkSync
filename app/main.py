from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app.name, version="1.0.0")

    app.include_router(api_router)

    @app.get("/", tags=["root"])
    async def index():
        return {"message": "Система по актуализации рабочего времени WorkTime Sync"}

    return app


app = create_app()

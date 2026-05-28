from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        summary=f"ANIME{''.join([str(i) for i in range(1, 68)])}",
        version="1.0.0",
    )

    app.include_router(api_router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "Ок"}

    return app


app = create_app()

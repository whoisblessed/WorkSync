from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(title=settings.app.name, version="1.0.0")


@app.get("/")
async def index():
    return {"message": "Система по актуализации рабочего времени WorkTime Sync"}

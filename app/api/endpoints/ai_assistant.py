from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_user_with_roles
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.models.user import Role
from app.repositories.availability_map import AvailabilityRepository
from app.repositories.risk_analytics import RiskAnalyticsRepository
from app.schemas.ai_assistant import (
    AIChatRequest,
    AIChatResponse,
    AIAnalysisRequest,
    AIAnalysisResponse,
)
from app.schemas.meeting_suggest import MeetingSuggestRequest, MeetingSuggestResponse
from app.services.ai_assistant import AIAssistantService
from app.services.meeting_suggest import MeetingSuggestService
from app.services.risk_analytics import RiskAnalyticsService

router = APIRouter(prefix="/ai", tags=["ai-assistant"])

DBSession = Annotated[AsyncSession, Depends(get_db)]


def _require_api_key() -> str:
    key = settings.deepseek_api_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DEEPSEEK_API_KEY не настроен в конфигурации сервера.",
        )
    return key


def _get_ai_service(session: DBSession) -> AIAssistantService:
    return AIAssistantService(
        api_key=_require_api_key(),
        repo=RiskAnalyticsRepository(session),
        risk_service=RiskAnalyticsService(),
    )


def _get_meeting_service(session: DBSession) -> MeetingSuggestService:
    return MeetingSuggestService(
        availability_repo=AvailabilityRepository(session),
        risk_repo=RiskAnalyticsRepository(session),
        api_key=_require_api_key(),
    )


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Чат с AI-ассистентом",
    description=(
        "Отправьте историю диалога и получите ответ ассистента. "
        "Если передан `employee_id` — ассистент загружает метрики этого сотрудника "
        "и отвечает в его контексте. Без `employee_id` — контекст всей команды. "
        "Доступно всем авторизованным пользователям."
    ),
)
async def chat(
    body: AIChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    ai_service: Annotated[AIAssistantService, Depends(_get_ai_service)],
) -> AIChatResponse:
    return await ai_service.chat(
        messages=body.messages,
        current_user=current_user,
        employee_id=body.employee_id,
        period_days=body.period_days,
    )


@router.post(
    "/analyze",
    response_model=AIAnalysisResponse,
    summary="AI-анализ рисков с объяснениями",
    description=(
        "Запускает полный AI-анализ команды (или одного сотрудника). "
        "Возвращает список рекомендаций с объяснениями и общее резюме по команде. "
        "Доступно для ролей: hr, manager."
    ),
)
async def analyze(
    body: AIAnalysisRequest,
    current_user: Annotated[User, Depends(get_user_with_roles(Role.hr, Role.manager))],
    ai_service: Annotated[AIAssistantService, Depends(_get_ai_service)],
) -> AIAnalysisResponse:
    return await ai_service.analyze(
        current_user=current_user,
        employee_id=body.employee_id,
        period_days=body.period_days,
    )


@router.post(
    "/suggest-meeting-time",
    response_model=MeetingSuggestResponse,
    summary="Подбор оптимального времени для встречи",
    description=(
        "Ищет топ-3 окна, когда максимальное число из указанных сотрудников доступны. "
        "Учитывает рабочий график, исключения (отпуска, больничные), занятые события "
        "и уровень перегрузки. Для каждого слота возвращает причины недоступности "
        "и предупреждения (поле warnings). "
        "Доступно для ролей: hr, manager."
    ),
)
async def suggest_meeting_time(
    body: MeetingSuggestRequest,
    current_user: Annotated[User, Depends(get_user_with_roles(Role.hr, Role.manager))],
    meeting_service: Annotated[MeetingSuggestService, Depends(_get_meeting_service)],
) -> MeetingSuggestResponse:
    return await meeting_service.suggest(
        employee_ids=body.employee_ids,
        duration_minutes=body.duration_minutes,
        days_ahead=body.days_ahead,
        current_user=current_user,
    )

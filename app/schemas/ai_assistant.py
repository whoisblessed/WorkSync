from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Annotated[
        Literal["user", "assistant"],
        Field(description="Роль отправителя сообщения"),
    ]
    content: Annotated[str, Field(description="Текст сообщения")]


class AIChatRequest(BaseModel):
    messages: Annotated[
        list[ChatMessage],
        Field(
            description=(
                "История диалога. Последний элемент — новый вопрос пользователя. "
                "Передавайте всю историю для поддержки контекста."
            )
        ),
    ]
    employee_id: Annotated[
        int | None,
        Field(
            default=None,
            description=(
                "Если указан — ассистент получает метрики конкретного сотрудника "
                "и отвечает в контексте его данных."
            ),
        ),
    ] = None
    period_days: Annotated[
        int,
        Field(
            default=30,
            ge=1,
            le=365,
            description="Период анализа событий (дни) для загрузки контекста",
        ),
    ] = 30


class AIChatResponse(BaseModel):
    answer: Annotated[str, Field(description="Ответ AI-ассистента")]
    context_used: Annotated[
        bool,
        Field(description="True — ассистент использовал реальные данные из системы"),
    ]


class AIAnalysisRequest(BaseModel):
    employee_id: Annotated[
        int | None,
        Field(
            default=None,
            description="ID сотрудника. None — анализ всей команды.",
        ),
    ] = None
    period_days: Annotated[int, Field(default=30, ge=1, le=365)] = 30


class AIRecommendation(BaseModel):
    employee_id: Annotated[int, Field(description="ID сотрудника")]
    full_name: Annotated[str, Field(description="ФИО сотрудника")]
    risk_level: Annotated[
        Literal["low", "medium", "high", "critical"],
        Field(description="Уровень риска"),
    ]
    integral_risk: Annotated[float, Field(description="Числовой показатель риска Ri")]
    ai_summary: Annotated[
        str,
        Field(description="AI-объяснение почему данный риск присвоен"),
    ]
    ai_actions: Annotated[
        list[str],
        Field(description="Конкретные действия, предложенные AI"),
    ]


class AIAnalysisResponse(BaseModel):
    recommendations: Annotated[
        list[AIRecommendation],
        Field(
            description="Список AI-рекомендаций по сотрудникам, приоритет — по убыванию риска"
        ),
    ]
    team_summary: Annotated[
        str,
        Field(description="Общее AI-резюме по команде"),
    ]

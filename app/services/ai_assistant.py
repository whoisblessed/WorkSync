from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx

from app.models import User
from app.models.user import Role
from app.repositories.risk_analytics import RiskAnalyticsRepository
from app.schemas.ai_assistant import (
    AIAnalysisResponse,
    AIRecommendation,
    AIChatResponse,
    ChatMessage,
)
from app.services.risk_analytics import RiskAnalyticsService, EmployeeRiskMetrics

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# Максимальный период для загрузки контекста
_MAX_PERIOD = 365

RISK_LABELS: dict[str, Literal["low", "medium", "high", "critical"]] = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}


def _risk_level(ri: float) -> Literal["low", "medium", "high", "critical"]:
    if ri < 0.3:
        return "low"
    if ri < 0.5:
        return "medium"
    if ri < 0.7:
        return "high"
    return "critical"


def _metrics_to_text(m: EmployeeRiskMetrics) -> str:
    """Превращает метрики одного сотрудника в читаемый текст для промпта."""
    name = f"{m.last_name} {m.first_name}" + (
        f" {m.patronymic}" if m.patronymic else ""
    )
    exc_str = ", ".join(m.active_exceptions) if m.active_exceptions else "нет"
    return (
        f"Сотрудник: {name} (ID={m.employee_id})\n"
        f"  Часовой пояс: {m.time_zone}, Формат: {m.work_format}\n"
        f"  Актуальность графика (Ai): {m.actuality_score:.2f} "
        f"(дней без обновления: {m.days_since_update})\n"
        f"  Встречи вне расписания (Ci): {m.out_of_schedule_ratio:.2f} "
        f"({m.meetings_out}/{m.meetings_total})\n"
        f"  Загрузка (Li): {m.load_level:.2f} "
        f"(занято {m.hours_busy:.1f}ч из {m.hours_work:.1f}ч)\n"
        f"  Конфликт TZ (Zi): {m.timezone_conflict:.2f}"
        + (f" — {m.timezone_note}" if m.timezone_note else "")
        + "\n"
        f"  Расхождение HR/календарь (Hi): {m.hr_calendar_mismatch:.2f}\n"
        f"  Интегральный риск (Ri): {m.integral_risk:.2f}\n"
        f"  Активные исключения: {exc_str}\n"
        f"  Системные рекомендации: {'; '.join(m.recommendations)}"
    )


def _build_system_prompt(metrics_block: str | None) -> str:
    base = (
        "Ты — AI-ассистент системы WorkTime Sync. "
        "Система помогает HR-специалистам и руководителям отслеживать актуальность "
        "рабочих графиков сотрудников, выявлять перегрузки, конфликты расписания "
        "и рекомендовать действия.\n\n"
        "Твоя задача:\n"
        "1. Отвечать на вопросы о доступности, рисках и расписании сотрудников.\n"
        "2. Объяснять, почему тот или иной показатель принял данное значение.\n"
        "3. Предлагать конкретные, объяснимые действия.\n"
        "4. Говорить кратко, по делу, на русском языке.\n"
        "5. Если данных нет — честно об этом сообщить.\n\n"
        "Используй следующие обозначения метрик при объяснении:\n"
        "  Ai — актуальность графика (1 = полностью актуален, 0 = устарел)\n"
        "  Ci — доля встреч вне рабочего времени\n"
        "  Li — уровень загрузки (>0.8 — перегрузка)\n"
        "  Zi — конфликт часового пояса\n"
        "  Hi — расхождение HR-данных и календаря\n"
        "  Ri — интегральный риск неактуальности (>0.6 — высокий)\n"
    )
    if metrics_block:
        base += (
            "\n--- ТЕКУЩИЕ ДАННЫЕ ИЗ СИСТЕМЫ ---\n"
            + metrics_block
            + "\n--- КОНЕЦ ДАННЫХ ---\n"
        )
    return base


async def _call_deepseek(
    api_key: str,
    system_prompt: str,
    messages: list[ChatMessage],
    max_tokens: int = 1024,
) -> str:
    payload = {
        "model": DEEPSEEK_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system_prompt}]
        + [{"role": m.role, "content": m.content} for m in messages],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


class AIAssistantService:
    def __init__(
        self,
        api_key: str,
        repo: RiskAnalyticsRepository,
        risk_service: RiskAnalyticsService,
    ) -> None:
        self.api_key = api_key
        self.repo = repo
        self.risk_service = risk_service

    # ------------------------------------------------------------------
    # Чат-ассистент
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[ChatMessage],
        current_user: User,
        employee_id: int | None,
        period_days: int,
    ) -> AIChatResponse:
        metrics_block: str | None = None
        context_used = False

        if employee_id is not None:
            m = await self._load_one(employee_id, period_days)
            if m is not None:
                metrics_block = _metrics_to_text(m)
                context_used = True
        else:
            # Загружаем всю команду (или всех для HR)
            manager_uid = current_user.id if current_user.role == Role.manager else None
            all_m = await self._load_all(manager_uid, period_days)
            if all_m:
                metrics_block = "\n\n".join(_metrics_to_text(m) for m in all_m)
                context_used = True

        system_prompt = _build_system_prompt(metrics_block)
        answer = await _call_deepseek(self.api_key, system_prompt, messages)
        return AIChatResponse(answer=answer, context_used=context_used)

    # ------------------------------------------------------------------
    # Пакетный AI-анализ с рекомендациями
    # ------------------------------------------------------------------

    async def analyze(
        self,
        current_user: User,
        employee_id: int | None,
        period_days: int,
    ) -> AIAnalysisResponse:
        manager_uid = current_user.id if current_user.role == Role.manager else None

        if employee_id is not None:
            m = await self._load_one(employee_id, period_days)
            metrics_list = [m] if m else []
        else:
            metrics_list = await self._load_all(manager_uid, period_days)

        # Сортируем по убыванию риска
        metrics_list.sort(key=lambda x: x.integral_risk, reverse=True)

        recommendations = await self._build_ai_recommendations(metrics_list)
        team_summary = await self._build_team_summary(metrics_list)

        return AIAnalysisResponse(
            recommendations=recommendations,
            team_summary=team_summary,
        )

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    async def _load_one(
        self, employee_id: int, period_days: int
    ) -> EmployeeRiskMetrics | None:
        now = datetime.now(tz=timezone.utc)
        period_start = now - timedelta(days=period_days)

        emps = await self.repo.get_employees_with_relations()
        emp = next((e for e in emps if e.id == employee_id), None)
        if emp is None:
            return None

        schedule = await self.repo.get_schedule_for_employee(emp.id)
        events = await self.repo.get_events_for_employee_in_period(
            emp.id, period_start, now
        )
        exceptions = await self.repo.get_exceptions_for_employee(emp.id)
        return self.risk_service.calculate_employee_metrics(
            emp, schedule, events, exceptions, period_days
        )

    async def _load_all(
        self, manager_user_id: int | None, period_days: int
    ) -> list[EmployeeRiskMetrics]:
        now = datetime.now(tz=timezone.utc)
        period_start = now - timedelta(days=period_days)

        emps = await self.repo.get_employees_with_relations(
            manager_user_id=manager_user_id
        )
        result = []
        for emp in emps:
            schedule = await self.repo.get_schedule_for_employee(emp.id)
            events = await self.repo.get_events_for_employee_in_period(
                emp.id, period_start, now
            )
            exceptions = await self.repo.get_exceptions_for_employee(emp.id)
            result.append(
                self.risk_service.calculate_employee_metrics(
                    emp, schedule, events, exceptions, period_days
                )
            )
        return result

    async def _build_ai_recommendations(
        self, metrics_list: list[EmployeeRiskMetrics]
    ) -> list[AIRecommendation]:
        if not metrics_list:
            return []

        # Формируем один запрос для всех сотрудников (экономим токены)
        employees_block = "\n\n".join(_metrics_to_text(m) for m in metrics_list)

        prompt_user = (
            "На основе данных ниже для каждого сотрудника:\n"
            "1. Определи уровень риска: low / medium / high / critical\n"
            "2. Напиши краткое объяснение (2-3 предложения) почему такой риск.\n"
            "3. Предложи 2-4 конкретных действия.\n\n"
            "Ответь строго в формате JSON-массива:\n"
            "[\n"
            "  {\n"
            '    "employee_id": <int>,\n'
            '    "risk_level": "<low|medium|high|critical>",\n'
            '    "ai_summary": "<текст объяснения>",\n'
            '    "ai_actions": ["<действие 1>", "<действие 2>"]\n'
            "  }\n"
            "]\n\n"
            "Данные сотрудников:\n" + employees_block
        )

        system = _build_system_prompt(None)
        raw = await _call_deepseek(
            self.api_key,
            system,
            [ChatMessage(role="user", content=prompt_user)],
            max_tokens=2048,
        )

        # Парсим JSON из ответа
        try:
            # DeepSeek может обернуть JSON в markdown-блок
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            items = json.loads(clean.strip())
        except Exception:
            # Если парсинг не удался — возвращаем базовые рекомендации
            return [
                AIRecommendation(
                    employee_id=m.employee_id,
                    full_name=f"{m.last_name} {m.first_name}",
                    risk_level=_risk_level(m.integral_risk),
                    integral_risk=m.integral_risk,
                    ai_summary="AI-анализ временно недоступен. Используйте системные рекомендации.",
                    ai_actions=m.recommendations,
                )
                for m in metrics_list
            ]

        # Собираем финальный список, дополняем данными из метрик
        metrics_by_id = {m.employee_id: m for m in metrics_list}
        result: list[AIRecommendation] = []
        for item in items:
            eid = item.get("employee_id")
            m = metrics_by_id.get(eid)
            if m is None:
                continue
            result.append(
                AIRecommendation(
                    employee_id=eid,
                    full_name=f"{m.last_name} {m.first_name}"
                    + (f" {m.patronymic}" if m.patronymic else ""),
                    risk_level=item.get("risk_level", _risk_level(m.integral_risk)),
                    integral_risk=m.integral_risk,
                    ai_summary=item.get("ai_summary", ""),
                    ai_actions=item.get("ai_actions", m.recommendations),
                )
            )
        return result

    async def _build_team_summary(self, metrics_list: list[EmployeeRiskMetrics]) -> str:
        if not metrics_list:
            return "Данные по команде отсутствуют."

        high_risk = [m for m in metrics_list if m.integral_risk >= 0.6]
        overloaded = [m for m in metrics_list if m.load_level > 0.8]
        outdated = [m for m in metrics_list if m.actuality_score < 0.5]

        stats = (
            f"Команда: {len(metrics_list)} чел. "
            f"Высокий риск: {len(high_risk)}. "
            f"Перегрузка: {len(overloaded)}. "
            f"Устаревший график: {len(outdated)}."
        )

        prompt_user = (
            f"Статистика команды: {stats}\n\n"
            "Напиши краткое (3-5 предложений) резюме по состоянию команды "
            "и главные приоритеты для HR/руководителя. На русском языке."
        )

        system = _build_system_prompt(None)
        return await _call_deepseek(
            self.api_key,
            system,
            [ChatMessage(role="user", content=prompt_user)],
            max_tokens=512,
        )

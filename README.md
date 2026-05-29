# WorkTime Sync — Backend API

REST API для системы контроля актуальности рабочих графиков сотрудников. Помогает HR-специалистам и руководителям отслеживать перегрузки, конфликты расписания и своевременно реагировать на отклонения.

## Технологический стек

- **Python 3.14** / **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy (async)** + **Alembic** — ORM и миграции базы данных
- **PostgreSQL** — основное хранилище данных
- **Pydantic v2 / pydantic-settings** — валидация данных и конфигурация через `.env`
- **JWT (HS256)** — аутентификация (access + refresh токены)
- **DeepSeek API** — LLM-движок для AI-ассистента и анализа рисков
- **httpx** — асинхронный HTTP-клиент для обращения к DeepSeek

---

## Структура проекта

```
app/
├── api/
│   ├── dependencies.py        # Зависимости FastAPI (авторизация, роли)
│   ├── router.py              # Сборка всех роутеров под /api
│   └── endpoints/
│       ├── auth.py            # Регистрация, логин, refresh токена
│       ├── user.py            # Управление пользователями
│       ├── employee.py        # Управление сотрудниками
│       ├── team.py            # Управление командами
│       ├── schedule.py        # Рабочие графики
│       ├── schedule_exception.py  # Исключения (отпуск, больничный и т.д.)
│       ├── event.py           # Календарные события
│       ├── profile.py         # Профиль текущего пользователя
│       ├── availability_map.py    # Карта доступности команды
│       └── ai_assistant.py    # AI-ассистент, анализ рисков, подбор времени встреч
├── core/
│   ├── config.py              # Настройки через pydantic-settings
│   ├── security.py            # Хэширование паролей, генерация JWT
│   └── exceptions.py          # Кастомные HTTP-исключения
├── db/
│   ├── base.py                # Декларативная Base для SQLAlchemy
│   ├── engine.py              # Создание async engine
│   └── session.py             # Фабрика сессий + dependency get_db
├── migrations/                # Alembic-миграции
├── models/                    # SQLAlchemy ORM-модели
│   ├── user.py                # User (роли: employee, manager, hr)
│   ├── employee.py            # Employee (ФИО, должность, команда)
│   ├── team.py                # Team
│   ├── schedule.py            # Schedule (рабочие дни, часы, часовой пояс)
│   ├── schedule_exception.py  # ScheduleException (отпуск, больничный и т.д.)
│   ├── event.py               # Event (календарные встречи)
│   └── employee_event.py      # M2M: сотрудник ↔ событие
├── repositories/              # Слой доступа к данным (async репозитории)
├── schemas/                   # Pydantic-схемы запросов и ответов
├── services/                  # Бизнес-логика
│   ├── auth.py
│   ├── employee.py
│   ├── event.py
│   ├── risk_analytics.py      # Расчёт метрик риска (Ai, Ci, Li, Zi, Hi, Ri)
│   ├── ai_assistant.py        # AI-ассистент и пакетный анализ
│   ├── meeting_suggest.py     # Подбор оптимального времени встречи
│   └── ...
└── main.py                    # Точка входа, создание FastAPI app
```

---

## AI-модуль

AI-модуль — интеллектуальное ядро системы WorkTime Sync, которое превращает сырые метрики расписания в понятные объяснения и конкретные действия. Он объединяет три возможности: чат-ассистент в реальном времени с доступом к данным команды, пакетный анализ рисков с ранжированием сотрудников и автоматическим подбором оптимального времени для встреч с учётом загрузки и исключений. В качестве LLM-движка используется DeepSeek — все запросы отправляются через `services/ai_assistant.py`, который формирует системный промпт, обогащённый актуальными метриками из базы данных.

### Эндпоинты (`/api/ai/`)

| Метод | Путь | Роли | Описание |
|-------|------|------|----------|
| POST | `/api/ai/chat` | все авторизованные | Чат с ассистентом; при передаче `employee_id` ответы строятся в контексте конкретного сотрудника |
| POST | `/api/ai/analyze` | hr, manager | Пакетный AI-анализ команды: уровень риска, объяснение, список действий для каждого сотрудника |
| POST | `/api/ai/suggest-meeting-time` | hr, manager | Топ-3 временных окна для встречи с учётом расписания, исключений и загрузки участников |

### Метрики риска (расчёт в `services/risk_analytics.py`)

| Метрика | Описание | Вес |
|---------|----------|-----|
| **Ai** | Актуальность графика (1 = актуален, 0 = устарел >90 дней) | 0.25 |
| **Ci** | Доля встреч вне рабочего времени | 0.25 |
| **Li** | Уровень загрузки (>0.8 — перегрузка) | 0.20 |
| **Zi** | Конфликт часового пояса | 0.15 |
| **Hi** | Расхождение HR-данных и реального календаря | 0.15 |
| **Ri** | Интегральный риск = взвешенная сумма выше (>0.6 — высокий) | — |

Уровни риска: `low` (<0.3) · `medium` (<0.5) · `high` (<0.7) · `critical` (≥0.7).

---

## Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
git clone <repo-url>
cd <repo-dir>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
APP__NAME=WorkTime Sync
APP__DEBUG=true

DATABASE__URL=postgresql+asyncpg://user:password@localhost:5432/worktime_sync
DATABASE__POOL_SIZE=10
DATABASE__MAX_OVERFLOW=20

JWT__SECRET_KEY=your-secret-key-here
JWT__ALGORITHM=HS256
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT__REFRESH_TOKEN_EXPIRE_DAYS=7

DEEPSEEK_API_KEY=your-deepseek-api-key
```

> AI-функции (`/api/ai/*`) работают только при наличии `DEEPSEEK_API_KEY`. Без него эндпоинты возвращают `503 Service Unavailable`.

### 3. Применение миграций

```bash
alembic upgrade head
```

### 4. Запуск сервера

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## Аутентификация

API использует JWT Bearer-токены.

```
POST /api/auth/register   — регистрация
POST /api/auth/login      — получение access + refresh токенов
POST /api/auth/refresh    — обновление access-токена
```

Передавайте токен в заголовке: `Authorization: Bearer <access_token>`

---

## Роли пользователей

| Роль | Доступ |
|------|--------|
| `employee` | Просмотр своего профиля, расписания, событий |
| `manager` | Управление своей командой, AI-анализ команды |
| `hr` | Полный доступ ко всем сотрудникам и AI-функциям |

---

## Основные эндпоинты

| Префикс | Описание |
|---------|----------|
| `/api/auth` | Аутентификация |
| `/api/users` | Управление пользователями |
| `/api/employees` | Сотрудники |
| `/api/teams` | Команды |
| `/api/schedules` | Рабочие графики |
| `/api/schedule-exceptions` | Исключения (отпуск, больничный и т.д.) |
| `/api/events` | Календарные события |
| `/api/profile` | Профиль текущего пользователя |
| `/api/availability-map` | Карта доступности команды |
| `/api/ai` | AI-ассистент, анализ рисков, подбор времени встреч |

---

## Пример запроса к AI-ассистенту

```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Кто из команды сейчас перегружен?"}
    ],
    "period_days": 30
  }'
```

Ответ:
```json
{
  "answer": "По данным за последние 30 дней перегружены 2 сотрудника: ...",
  "context_used": true
}
```

---

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|:------------:|----------|
| `DATABASE__URL` | ✅ | URL подключения к PostgreSQL |
| `JWT__SECRET_KEY` | ✅ | Секретный ключ для подписи JWT |
| `DEEPSEEK_API_KEY` | ⬜ | Ключ API DeepSeek (нужен для AI-функций) |
| `APP__DEBUG` | ⬜ | Режим отладки (по умолчанию `true`) |
| `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` | ⬜ | Время жизни access-токена (по умолчанию 30) |
| `JWT__REFRESH_TOKEN_EXPIRE_DAYS` | ⬜ | Время жизни refresh-токена (по умолчанию 7) |

---

## Лицензия

Проект разработан в учебных/рабочих целях. Лицензия не определена.

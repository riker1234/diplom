# ПодборПериферии

Веб-приложение для сравнения цен и подбора компьютерной периферии. Агрегирует товары с Ozon, Wildberries и Ситилинка, позволяет фильтровать каталог и получать персональные рекомендации через интерактивный опросник.

## Возможности

- Каталог товаров по 6 категориям: мыши, клавиатуры, мониторы, наушники, микрофоны, коврики
- Сравнение цен сразу с трёх магазинов на одной странице
- Фильтрация по магазину, цене и характеристикам
- Система рекомендаций на основе ответов пользователя (без ML-библиотек)
- Автоматический парсинг данных с Ozon, Wildberries и Ситилинка

## Стек технологий

**Бэкенд:**
- Python, FastAPI
- PostgreSQL, SQLAlchemy ORM, Alembic
- Selenium (Ozon, Wildberries), httpx (Ситилинк)

**Фронтенд:**
- React, TypeScript
- Tailwind CSS, Vite

## Структура проекта

```
diplom/
├── backend/
│   ├── app/
│   │   ├── routers/        (API эндпоинты)
│   │   ├── models/         (SQLAlchemy модели)
│   │   ├── schemas/        (Pydantic схемы)
│   │   ├── parsers/        (парсеры Ozon / WB / Ситилинк)
│   │   └── recommendation/ (движок рекомендаций)
│   └── alembic/            (миграции БД)
└── frontend/
    └── src/
        ├── pages/          (Каталог, Главная, Опросник, Результаты)
        └── components/     (ProductModal и др.)
```

## Запуск

### Бэкенд

```bash
cd backend
pip install -r requirements.txt

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload
```

API доступно на `http://localhost:8000`  
Swagger документация: `http://localhost:8000/docs`

### Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Приложение откроется на `http://localhost:5173`

## Основные API эндпоинты

| Эндпоинт | Описание |
|----------|----------|
| `GET /mice/` | Список мышей с фильтрами |
| `GET /keyboards/` | Список клавиатур |
| `GET /monitors/` | Список мониторов |
| `GET /headphones/` | Список наушников |
| `GET /microphones/` | Список микрофонов |
| `GET /mousepads/` | Список ковриков |
| `POST /recommendation/` | Получить рекомендации по опроснику |

Все эндпоинты каталога поддерживают параметры `price_min` и `price_max`.

# Бэкенд с chromium для точечного перепарса цен (кнопка «Обновить цену»).
# Railway автоматически использует этот Dockerfile вместо Nixpacks.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# $PORT подставляет Railway; локально — 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

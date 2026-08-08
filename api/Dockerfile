FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
# DejaVu — шрифт с кириллицей для генерации og:image (content/og.py)
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# dev: hot-reload через runserver + volume-mount кода (см. docker-compose.yml)
FROM base AS dev
COPY requirements-dev.txt ./
RUN uv pip install --system -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod
COPY . .
# collectstatic на этапе сборки: манифест whitenoise попадает в образ
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && useradd --create-home appuser \
    && mkdir -p /app/media && chown appuser /app/media
USER appuser
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

# psycopg[binary] (backend/pyproject.toml) ships its own libpq build, so this
# image needs no compiler toolchain or libpq-dev — a deliberate dependency
# choice that keeps the image simple. Revisit only if a future dependency
# genuinely needs one; don't add build-essential speculatively.

WORKDIR /app

RUN groupadd --system gymcompanion \
    && useradd --system --gid gymcompanion --create-home --home-dir /home/gymcompanion gymcompanion

COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN chown -R gymcompanion:gymcompanion /app
USER gymcompanion

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

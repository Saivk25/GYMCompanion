# syntax=docker/dockerfile:1
FROM python:3.14-slim AS runtime

# psycopg[binary] (backend/pyproject.toml) ships its own libpq build, so this
# image needs no compiler toolchain or libpq-dev — a deliberate dependency
# choice that keeps the image simple. Revisit only if a future dependency
# genuinely needs one; don't add build-essential speculatively.

WORKDIR /app

RUN groupadd --system gymcompanion \
    && useradd --system --gid gymcompanion --create-home --home-dir /home/gymcompanion gymcompanion

# requirements-lock.txt (hash-pinned, see README.md's "Reproducible builds")
# is what actually gets installed, not pyproject.toml's ranges resolved
# fresh at build time — otherwise this image, the artifact that actually
# ships, would be the one place in the whole reproducible-builds story that
# wasn't reproducible. pyproject.toml is still copied and installed
# --no-deps right after, so the image also has an installed
# gym-companion-backend distribution (needed for its own metadata), without
# letting that second install re-resolve anything.
COPY pyproject.toml requirements-lock.txt README.md ./
RUN pip install --no-cache-dir -r requirements-lock.txt \
    && pip install --no-cache-dir --no-deps .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN chown -R gymcompanion:gymcompanion /app
USER gymcompanion

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

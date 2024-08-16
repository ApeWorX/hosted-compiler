FROM python:3.11 AS base

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create virtualenv using poetry lockfile
FROM base AS builder

ENV PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1

RUN pip install "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.in-project true
COPY poetry.lock pyproject.toml /app/

RUN poetry install --only main --no-interaction --no-root

# Create runtime image
FROM python:3.11-slim AS runtime

ARG GITHUB_TOKEN
ENV GITHUB_TOKEN=${GITHUB_TOKEN} \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH
COPY --from=builder /app/.venv /app/.venv

COPY main.py vvm_versions.py /app/
RUN python3 vvm_versions.py

ENTRYPOINT ["uvicorn", "main:app",  "--host", "0.0.0.0", "--port", "8000"]

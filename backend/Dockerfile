# ============================================================
# Global Avícola — Backend Dockerfile
# Multi-stage build for FastAPI
# ============================================================

# ----- Stage 1: Build dependencies -----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ----- Stage 2: Runtime -----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r avicola && useradd -r -g avicola avicola

# Copy dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/
COPY seeds/ seeds/
COPY scripts/ scripts/

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# SPEC 016 §B: procedencia del build. El SHA y la fecha llegan por `build-arg` porque la
# imagen no contiene `.git`: preguntarle al repositorio en tiempo de ejecución no diría qué
# se construyó. Van después de los COPY y de los ENV de dependencias para no invalidar la
# caché de capas cuando solo cambia el commit. `GET /api/v1/version` los publica.
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
ENV GA_GIT_SHA=$GIT_SHA
ENV GA_BUILD_TIME=$BUILD_TIME
LABEL org.opencontainers.image.revision=$GIT_SHA
LABEL org.opencontainers.image.created=$BUILD_TIME

# Expose port
EXPOSE 8000

# GA-REM-024: el entrypoint aplica las migraciones antes de ceder el control al servidor.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Run as non-root
USER avicola

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start server.
#
# El ENTRYPOINT migra y ejecuta el CMD. Los servicios que declaran su propio `command`
# —el bot de Telegram, que comparte esta imagen— pasan igualmente por la migracion, que es
# idempotente y por tanto inocua para ellos.
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

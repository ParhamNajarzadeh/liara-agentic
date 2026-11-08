# ==============================================================================
# Multi-Stage Production Dockerfile for Liara PaaS Deployment
# Keeps the Liara Agentic SRE Assistant online 24/7 during Hackathon Judging
# within the 2,000,000 Tomans credit budget (ir-standard-1g / ir-mini).
# ==============================================================================

FROM python:3.11-slim AS backend-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx pydantic pydantic-settings

COPY src/ ./src/
COPY .claude/ ./.claude/
COPY .mcp.json ./
COPY CLAUDE.md MEMORY.md README.md RUNBOOK.md ./
COPY workspace/ ./workspace/
COPY eval/ ./eval/
COPY scripts/ ./scripts/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

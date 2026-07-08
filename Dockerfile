# ---------- Builder ----------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip uv

COPY . .

RUN uv sync --frozen

# ---------- Runtime ----------
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8080
ENV SERVER_HOST=0.0.0.0

USER appuser

CMD ["python", "-m", "src.server.databricks_http_server"]

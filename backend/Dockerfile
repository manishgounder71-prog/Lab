FROM python:3.14-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose the API port
EXPOSE 8000

# Health check — uses the port the app is actually listening on (from $PORT or 8000)
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD sh -c "curl -sf http://localhost:${PORT:-8000}/ || exit 1"

# Run the FastAPI server — respects Render's $PORT env var (fallback 8000)
CMD sh -c "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

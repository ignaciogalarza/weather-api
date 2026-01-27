FROM python:3.12.8-slim

WORKDIR /app

# Install uv via pip (pinned version for reproducibility)
RUN pip install --no-cache-dir uv==0.5.14

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/

# Install the project
RUN uv sync --frozen --no-dev

# Create non-root user for security with home directory for cache
RUN addgroup --system --gid 1000 app && \
    adduser --system --uid 1000 --gid 1000 --home /home/app app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Set environment for UV cache (writable by non-root user)
ENV HOME=/home/app

# Expose port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "weather_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

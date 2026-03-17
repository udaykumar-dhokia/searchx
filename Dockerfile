FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Copy dependency files and metadata needed for build
COPY pyproject.toml uv.lock README.md ./
COPY trawl/__init__.py trawl/__init__.py

# Install dependencies
RUN /uv/bin/uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Expose the backend port
EXPOSE 8000

# Run the FastAPI server
CMD ["/uv/bin/uv", "run", "trawl-api"]

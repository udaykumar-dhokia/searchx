FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN /uv/bin/uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Expose the backend port
EXPOSE 8000

# Run the FastAPI server
CMD ["fastapi", "run", "src/main.py", "--port", "8000", "--host", "0.0.0.0"]

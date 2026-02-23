FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy entire repo
COPY . .

# Go to backend directory (where pyproject.toml exists)
WORKDIR /app/apps/web/backend

# Disable venv (important for Docker)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Remove PyPI withoutbg if installed
RUN pip uninstall -y withoutbg || true

# Install local project
RUN pip install -e /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

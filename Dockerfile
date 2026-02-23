FROM python:3.10-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy repo
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r apps/web/backend/requirements.txt

# Remove conflicting PyPI package if exists
RUN pip uninstall -y withoutbg || true
RUN pip install -e .

WORKDIR /app/apps/web/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
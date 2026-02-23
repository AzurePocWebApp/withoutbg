FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY . .

WORKDIR /app/apps/web/backend

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# 👇 Important: expose root so "withoutbg" module is found
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

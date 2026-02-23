FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY . .

WORKDIR /app/apps/web/backend

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

RUN pip uninstall -y withoutbg || true
RUN pip install -e /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

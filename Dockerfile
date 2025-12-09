FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements /app/requirements
RUN pip install --upgrade pip \
    && pip install -r /app/requirements

COPY . /app

# Открываем порт для вебхуков (если понадобится)
EXPOSE 8080

CMD ["python", "main.py"]


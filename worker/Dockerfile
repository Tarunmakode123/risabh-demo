FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY ../backend/requirements.txt ./backend_requirements.txt
RUN pip install --no-cache-dir -r backend_requirements.txt
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

COPY . /app/worker
COPY ../backend /app/backend

ENV PYTHONPATH=/app:/app/backend

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "-Q", "imap,email_processing,cta,reply"]

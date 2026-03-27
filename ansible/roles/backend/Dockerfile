# NetMonitor Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY ../../app /app/app
COPY ../../requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Entrypoint expects .env to be mounted or copied in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

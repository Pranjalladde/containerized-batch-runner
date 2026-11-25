FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/ app/
COPY tasks/ tasks/
COPY config/ config/

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser
ENTRYPOINT ["python"]
CMD ["-m", "app.worker", "task_1"]

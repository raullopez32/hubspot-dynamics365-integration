FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src ./src
COPY config ./config

ENV PORT=8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} src.app:app"]

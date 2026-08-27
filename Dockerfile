FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
RUN useradd --create-home --shell /usr/sbin/nologin appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app ./app
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"10000\")}/health')"
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

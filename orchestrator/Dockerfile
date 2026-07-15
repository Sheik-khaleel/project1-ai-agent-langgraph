FROM python:3.12-slim

WORKDIR /app

COPY orchestrator/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY orchestrator /app/orchestrator

CMD ["uvicorn", "orchestrator.app:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.12-slim

WORKDIR /app

COPY sink-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY sink-api/ ./

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
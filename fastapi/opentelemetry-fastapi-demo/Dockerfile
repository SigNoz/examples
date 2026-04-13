FROM python:3.13-slim

EXPOSE 5002

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]

FROM tiangolo/uvicorn-gunicorn:python3.12

EXPOSE 5002

COPY ./app/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY ./app /app/app

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"]

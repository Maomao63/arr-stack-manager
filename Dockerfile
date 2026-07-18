FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn jinja2 python-multipart
# Wir kopieren den Code nicht mehr per COPY, 
# da er durch das Volume vom Host überschrieben wird
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Erstellt die config.json und gibt Schreibrechte
RUN touch config.json && chmod 666 config.json
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

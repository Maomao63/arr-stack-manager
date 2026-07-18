FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Statt uvicorn-Modul-Import nutzen wir den direkten Dateiaufruf
CMD ["python3", "main.py"]

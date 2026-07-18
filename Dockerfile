FROM python:3.12-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den gesamten Inhalt des Repo-Ordners in das Arbeitsverzeichnis kopieren
COPY . .

# Sicherstellen, dass config.json existiert und beschreibbar ist
RUN touch /app/config.json && chmod 666 /app/config.json

# Anwendung starten
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

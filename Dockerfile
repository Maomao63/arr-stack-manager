FROM python:3.12-slim
WORKDIR /app
COPY . .
# Wir zwingen ihn, alle Dateien im /app Ordner anzuzeigen
RUN ls -R /app
CMD ["echo", "Debug-Modus beendet"]

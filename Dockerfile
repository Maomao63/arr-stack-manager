FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/Maomao63/arr-stack-manager" \
      org.opencontainers.image.description="Dashboard for finding duplicates across Sonarr and Radarr instances"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Persistente Daten werden getrennt vom Programmcode unter /config abgelegt.
RUN mkdir -p /config
ENV CONFIG_DIR=/config
VOLUME ["/config"]
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```services:
  arr-stack-manager:
    build: .
    container_name: arr-stack-manager
    restart: unless-stopped
    ports:
      - "5005:8000"
    volumes:
      - /mnt/user/appdata/arr-stack-manager:/app
    environment:
      - TZ=Europe/Berlin```

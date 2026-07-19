# 🚀 Arr-Stack-Manager

The **Arr-Stack-Manager** is your centralized hub for managing your media automation ("Arr" suite) services. This lightweight tool provides a clear dashboard to monitor and control your stack efficiently.

## 🛠 Features
* **Centralized Dashboard**: Manage all your services from a single interface.
* **Simple Deployment**: Ready to run in seconds using Docker Compose.
* **Lightweight**: Built on Python Slim for a minimal resource footprint.

---

## 📦 Installation

Setup Instructions

    Create a project directory and navigate into it:

Bash

mkdir arr-stack-manager && cd arr-stack-manager

    Create a compose.yaml file with the following content:

YAML

services:
  arr-stack-manager:
    build: 
      context: [https://github.com/Maomao63/arr-stack-manager.git#main](https://github.com/Maomao63/arr-stack-manager.git#main)
    container_name: arr-stack-manager
    restart: unless-stopped
    ports:
      - "5005:8000"
    volumes:
      - ./config:/config
    environment:
      - TZ=Europe/Berlin

    Launch the container:

Bash

docker compose up -d

    Access your dashboard at:

Plaintext

http://<YOUR-HOST-IP>:5005

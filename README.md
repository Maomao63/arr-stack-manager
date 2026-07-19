# 🚀 Arr-Stack-Manager

The **Arr-Stack-Manager** is your centralized hub for managing your media automation ("Arr" suite) services. This lightweight tool provides a clear dashboard to monitor and control your stack efficiently.

## 🛠 Features
* **Centralized Dashboard**: Manage all your services from a single interface.
* **Simple Deployment**: Ready to run in seconds using Docker Compose.
* **Lightweight**: Built on Python Slim for a minimal resource footprint.

---

## 📦 Installation

You can get the stack up and running in just a few steps.

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) must be installed on your host.

### Setup Instructions

1. Create a project directory and navigate into it:
```bash
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
      # Path to your configuration folder
      - ./config:/config
    environment:
      - TZ=Europe/Berlin

    Launch the container:

Bash

docker compose up -d

    Access your dashboard at:

Plaintext

http://<YOUR-HOST-IP>:5005

⚙️ Configuration

The ./config folder will be created automatically upon the first launch and contains your config.json. You can adjust your settings there at any time.
📝 License

Open Source & DIY. Happy automating!

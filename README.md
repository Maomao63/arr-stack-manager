# 🚀 Arr Stack Manager

Arr Stack Manager is a lightweight web dashboard that checks two instances of
the same application for duplicate content. It compares Sonarr A with Sonarr B
and Radarr A with Radarr B, then shows series or movies that exist in both
instances. Duplicates can be removed from the configured primary instance.

## What the application compares

The application is designed for users who operate two separate instances of
Sonarr, Radarr, or both:

| Primary instance | Reference instance | Duplicate identifier |
| --- | --- | --- |
| Sonarr A | Sonarr B | TVDB ID |
| Radarr A | Radarr B | TMDB ID |

An item is considered a duplicate when the same identifier exists in both
instances. Instance A is the primary instance where deletion is available.
Instance B is only used as the comparison reference and is not modified.

## Features

- Check two Sonarr instances for duplicate series by TVDB ID
- Check two Radarr instances for duplicate movies by TMDB ID
- Show the file and episode status of matching items
- Remove items and their files from the configured primary instance
- Keep a history of the last 100 deletions
- Store all persistent data in a freely selectable host directory
- Run as a small Docker container based on Python Slim

## How persistence works

The application and its templates are part of the Docker image. Only data that
must survive container updates is written to `/config` inside the container.

The selected host directory will contain:

| File | Purpose |
| --- | --- |
| `config.json` | Sonarr/Radarr URLs and API keys |
| `history.json` | The last 100 deletion events |

Recreating or updating the container does not remove these files as long as the
same host directory is mounted to `/config`.

## Requirements

- Docker Engine or Docker Desktop
- Docker Compose v2
- Network access from the container to the configured Sonarr/Radarr instances

## Installation with Docker Compose

Create a new directory for the Compose project and save the following content as
`compose.yaml`:

```yaml
services:
  arr-stack-manager:
    build:
      context: https://github.com/Maomao63/arr-stack-manager.git#main
      pull: true
    pull_policy: build
    container_name: arr-stack-manager
    restart: unless-stopped
    ports:
      - "5005:8000"
    volumes:
      - "${CONFIG_PATH:-./config}:/config"
    environment:
      TZ: "${TZ:-Europe/Berlin}"
```

Start the application:

```bash
docker compose up -d --build
```

Open the dashboard at:

```text
http://localhost:5005
```

When Docker runs on another server, replace `localhost` with that server's IP
address or hostname.

## Choosing the config directory

If `CONFIG_PATH` is not set, persistent files are stored in a `config` directory
next to `compose.yaml`:

```text
arr-stack-manager/
├── compose.yaml
└── config/
    ├── config.json
    └── history.json
```

To choose another location, create a file named `.env` next to `compose.yaml`:

```env
CONFIG_PATH=/path/to/arr-stack-manager
TZ=Europe/Berlin
```

Example paths:

```env
# Linux
CONFIG_PATH=/opt/arr-stack-manager

# Unraid
CONFIG_PATH=/mnt/user/appdata/arr-stack-manager

# Windows with Docker Desktop
CONFIG_PATH=C:/docker/arr-stack-manager
```

Only change the host path. The container path must remain `/config`.

You can verify the resolved configuration before starting the container:

```bash
docker compose config
```

## First-time setup

1. Open the dashboard in your browser.
2. Select **Settings**.
3. Enter the URL and API key for both Sonarr instances.
4. Enter the URL and API key for both Radarr instances.
5. Save the configuration.

Instance A is the primary instance from which items can be deleted. Instance B
is used as the comparison reference. The container must be able to reach the
URLs entered in Settings.

## Updating

`restart: unless-stopped` only restarts the existing container. It does not fetch
changes from GitHub. This project builds an image directly from the Git repository,
so a platform's **Pull Image** action does not update it either.

The Compose template uses `pull_policy: build` to rebuild the application image
when the stack is deployed, even if a previously built image already exists.
`build.pull: true` also checks for a newer Python base image.

Deploy the stack again, or run the following command, to install the newest
version from the `main` branch:

```bash
docker compose up -d --build
```

To force a completely clean rebuild, use:

```bash
docker compose build --no-cache --pull
docker compose up -d --force-recreate
```

If a deployment platform still reuses stale build layers, temporarily add
`no_cache: true` below `pull: true`:

```yaml
build:
  context: https://github.com/Maomao63/arr-stack-manager.git#main
  pull: true
  no_cache: true
```

Remove `no_cache: true` after the successful rebuild. Leaving it enabled makes
every future deployment slower because all Dockerfile layers are rebuilt.

The files in the configured host directory remain intact during an update.

## Useful commands

View container status:

```bash
docker compose ps
```

Follow application logs:

```bash
docker compose logs -f arr-stack-manager
```

Restart the application:

```bash
docker compose restart arr-stack-manager
```

Stop and remove the container:

```bash
docker compose down
```

This does not delete the configured host directory.

## Troubleshooting

### The dashboard does not open

Check that the container is running and review its logs:

```bash
docker compose ps
docker compose logs arr-stack-manager
```

Also make sure port `5005` is not already used by another application. You can
change the host port without changing the container port:

```yaml
ports:
  - "8080:8000"
```

### Sonarr or Radarr cannot be reached

- Verify the URL and API key in Settings.
- Make sure the URL is reachable from inside Docker.
- Do not use `localhost` for another container or host service unless the
  service actually runs inside the Arr Stack Manager container.
- When services share a Docker network, use their Compose service names.

### Configuration is lost after an update

Confirm that the volume maps a persistent host directory to `/config`:

```yaml
volumes:
  - "${CONFIG_PATH:-./config}:/config"
```

Do not mount the appdata directory to `/app`; that would hide the application
code included in the image.

## Security notice

The current application does not provide user authentication. Keep it on a
trusted private network or protect it with an authenticated reverse proxy. Do
not expose it directly to the public internet.

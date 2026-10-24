# CLAUDE.md

## What this repo is

A Python WebSocket server that bridges my website and mobile app to an MQTT broker for real-time irrigation sensor updates. Clients connect over WebSocket, and the server relays messages to and from Mosquitto MQTT topics. On connect, it replays the last known irrigation state and queue so clients are immediately up to date.

## How it fits

This is one service in a larger home automation and irrigation system. Related repos:

- **home-server.api** — Flask REST API for schedules, zones, history, and devices
- **home-server.infra** — Docker Compose for shared infrastructure (MySQL, MongoDB, Mosquitto, nginx)
- **irrigation-controller** — Raspberry Pi service that manages the irrigation priority queue
- **garden-controller** — Raspberry Pi Zero 2W that controls GPIO relays
- **irrigation-automation.service** — Schedule runner that triggers irrigations via MQTT
- **home-server.mobile** — React Native mobile app
- **home-server.web** — React web app

All home server services join the shared Docker network defined in home-server.infra.

## Stack

- Python 3.9
- websockets (async WebSocket server)
- paho-mqtt (MQTT client)
- PyJWT (token authentication)
- python-dotenv (environment config)
- Docker and Docker Compose

## Commands

```bash
# Run with Docker (production)
docker compose up -d

# Run locally (development)
pip install -r requirements.txt
python index.py

# Lint (after phase 5)
ruff check .
ruff format --check .

# Test (after phase 4)
pytest
```

## Folder layout

```
index.py                 Main server, WebSocket + MQTT bridge
config/config.py         Environment-based configuration
ObjectTypes.py           TypedDict definitions for irrigation data
Dockerfile               Python 3.9 container image
docker-compose.yaml      Service definition, joins home-server network
requirements.txt         Python dependencies
docs/specs/              Feature and change specifications
```

## Environment variables

Defined in `.env` at the repo root, loaded by python-dotenv.

| Variable | Purpose | Example |
|---|---|---|
| `MQTT_BROKER` | Hostname or IP of the Mosquitto MQTT broker | `mosquitto` |
| `JWT_SECRET` | Secret key for verifying JWT tokens | (generate a random hex string) |
| `DEVICE_NAME` | Name this service reports in health check responses | `irrigation_webserver` |

## Standards

- Two long-lived branches. `main` holds stable code, `dev` holds ongoing work. Spec branches are named `spec/NNN-short-name`, come off `dev`, and merge back into `dev`.
- Commit messages are imperative, sentence case, under 60 characters, no trailing period.
- Python uses ruff for lint and format, pytest for tests.
- `.gitignore` covers `.env` and `secrets/`.
- No secrets, real IPs, or credentials in committed code.

## Workflow

Changes start as specs in `docs/specs/`. Claude Code implements them on a spec branch, and I review and merge every pull request.

## Ground rules

- Never push to GitHub. I do all pushing.
- Never change app behavior unless a spec says to.
- Never commit `.env` files, secrets, real domains, real IP addresses, or hostnames.
- Never merge a pull request. I review and merge every one.
- Only write things that are true in the code.

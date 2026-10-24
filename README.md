[![CI](https://github.com/Buie-Dev/home-server.websocket/actions/workflows/ci.yml/badge.svg)](https://github.com/Buie-Dev/home-server.websocket/actions/workflows/ci.yml)

# home-server.websocket

Python WebSocket server that bridges my website and mobile app to MQTT for real-time irrigation sensor updates.

## Why I built it

I have live flow sensors on my irrigation system and I wanted updates to reach the app and website immediately. Polling a REST API would add latency and unnecessary load, so I built this server to relay MQTT messages over WebSocket in real time. When a client connects it replays the last known irrigation state and queue so the UI is up to date right away.

## How it fits

This is one service in a larger home irrigation and automation system.

- [home-server.api](https://github.com/Buie-Dev/home-server.api) is the Flask REST API for schedules, zones, history, and devices
- [home-server.infra](https://github.com/Buie-Dev/home-server.infra) runs shared infrastructure with Docker Compose (MySQL, MongoDB, Mosquitto, nginx)
- [home-server.mobile](https://github.com/Buie-Dev/home-server.mobile) is the React Native mobile app
- [home-server.web](https://github.com/Buie-Dev/home-server.web) is the React web app
- [irrigation-controller](https://github.com/Buie-Dev/irrigation-controller) manages the priority queue on a Raspberry Pi
- [garden-controller](https://github.com/Buie-Dev/garden-controller) controls GPIO relays on a Raspberry Pi Zero 2W
- [irrigation-automation.service](https://github.com/Buie-Dev/irrigation-automation.service) triggers scheduled irrigations via MQTT

All home server services join the shared Docker network defined in home-server.infra.

## Stack

- Python 3.9
- websockets (async WebSocket server)
- paho-mqtt (MQTT client)
- PyJWT (token authentication)
- python-dotenv (environment config)
- Docker and Docker Compose

## Running it locally

Start the shared infrastructure in home-server.infra first so the Docker network and Mosquitto broker are available.

```bash
# With Docker
docker compose up -d

# Without Docker
pip install -r requirements.txt
python index.py
```

## Configuration

Environment variables are defined in `.env` at the repo root. See `.env.example` for the template.

| Variable | Purpose | Example |
|---|---|---|
| `MQTT_BROKER` | Hostname or IP of the Mosquitto MQTT broker | `mosquitto` |
| `JWT_SECRET` | Secret key for verifying JWT tokens from clients | (random hex string) |
| `DEVICE_NAME` | Name reported in health check responses | `irrigation_webserver` |

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests mock all external dependencies (MQTT broker, WebSocket connections) and run without any services.

## How I work on it

Changes start as specs in `docs/specs/`. Claude Code implements them on a branch, and I review and merge every pull request.

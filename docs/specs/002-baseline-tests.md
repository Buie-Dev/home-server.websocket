# 002 Baseline Tests

## Goal

Add tests that lock in how the code behaves today, before any other changes.

## Context

The server has three main areas of logic: JWT/IP authentication, MQTT message routing to WebSocket clients, and WebSocket message routing to MQTT. All external dependencies (MQTT broker, WebSocket connections) must be mocked.

## Scope

- Add pytest as the test framework with a `pyproject.toml` test config and `requirements-dev.txt`.
- Add a `conftest.py` with shared fixtures (mock MQTT client, mock WebSocket, patched Config).
- Test `is_internal_ip` for internal and external IPs.
- Test `authenticate` for internal IPs (bypass), valid JWT, expired JWT, missing token, and invalid token.
- Test `on_connect` subscribes to all expected MQTT topics.
- Test `on_message` routes each MQTT topic to the correct WebSocket topic and caches currentState and priorityQueue.
- Test `on_message` responds to healthcheck/request by publishing to healthcheck/response.
- Test `websocket_handler` replays cached state on connect, rejects unauthorized clients, routes WebSocket messages to the correct MQTT topics, and broadcasts rowing topics.
- Mock all external dependencies (MQTT client, WebSocket connections, Config values).

## Out of scope

- Changing any application code.
- Integration tests requiring a real MQTT broker or WebSocket server.

## Acceptance criteria

- `pytest` runs and all tests pass.
- All external dependencies are mocked.
- No application code is changed.

## Test plan

- Run `pytest -v` and confirm all tests pass.

## Notes

Likely bugs to investigate in Phase 6:
- `asyncio.run()` called inside `on_message` MQTT callback. This will fail if an event loop is already running, which is the case since the WebSocket server runs on asyncio. Should use `asyncio.get_event_loop().call_soon_threadsafe()` or similar.
- `broadcast_message` uses `asyncio.wait()` without wrapping coroutines in tasks, which is deprecated.
- `CURRENT_STATE` and `PRIORITY_QUEUE` are stored as raw strings but type-hinted as `CurrentState`/`PriorityQueue` (typed dicts). They're never parsed from JSON.
- Debug print statements throughout (`"Here -------------"`, `"DISONCECEOINC"`, `"onMessage"`).
- `"Boradcasting"` typo in print statement.
- `is_internal_ip` matching `"172."` is overly broad (matches all 172.x.x.x, not just 172.16-31.x.x).

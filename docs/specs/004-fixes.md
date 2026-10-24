# 004 Fixes

## Goal

Fix bugs identified in spec 002, remove debug prints, and report gitleaks findings.

## Context

Baseline tests documented several bugs and code quality issues. The codebase also has debug print statements that should not be in production code.

## Scope

### Bug fixes (one fix per commit, test-first)
1. **`asyncio.run()` in MQTT callback** — `on_message` calls `asyncio.run(broadcast_message(...))` which fails if an event loop is already running (which it always is, since the WebSocket server runs on asyncio). Replace with thread-safe scheduling into the running loop.
2. **`asyncio.wait()` with bare coroutines** — `broadcast_message` passes coroutines directly to `asyncio.wait()`, which is deprecated since Python 3.8. Wrap in `asyncio.create_task()`.
3. **Unknown MQTT topic broadcasts empty string** — `on_message` broadcasts with `web_socket_topic = ""` when the topic doesn't match any known pattern. Add an early return for unmatched topics.

### Cleanup (single commit)
4. **Remove debug prints** — Remove `"Here -------------"`, `"DISONCECEOINC"`, `"onMessage"`, `"Boradcasting"` typo print, and other verbose debug prints. Replace with minimal logging or remove entirely.

### Gitleaks findings
5. One finding: `JWT_SECRET` value committed in `.env` in the old history (commit `5b6fc03`). The `.env` was later removed from tracking and added to `.gitignore`. The secret is still in the git history.

## Out of scope

- Rewriting git history to remove the leaked secret (your decision).
- Fixing the broad `172.` IP prefix match (functional but overly permissive, low risk on a home network).

## Acceptance criteria

- `asyncio.run()` replaced with thread-safe event loop scheduling.
- `broadcast_message` wraps coroutines in tasks.
- Unknown MQTT topics do not broadcast empty-topic messages.
- All debug prints removed.
- All existing tests updated and passing.
- `ruff check .` and `ruff format --check .` clean.

## Test plan

- For each bug fix, update or add a test that fails first, then fix the code.
- Run full test suite after all changes.

## Notes

- The leaked JWT_SECRET in history should be rotated on the actual server regardless of whether history is rewritten.

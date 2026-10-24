# 001 Project Setup

## Goal

Set up project documentation and contribution templates so the repo is easy to understand and contribute to.

## Context

This is a small Python WebSocket server that bridges a React Native mobile app and a web app to an MQTT broker for real-time irrigation sensor updates. It is part of a larger home automation project with several related repos. There are no existing docs, spec templates, or PR templates.

## Scope

- Create `CLAUDE.md` covering what the repo is, how it fits with related repos, stack and versions, commands to install/run/lint/test, folder layout, coding standards, ground rules, and the spec workflow.
- Create `docs/specs/000-template.md` with the standard spec sections.
- Create `.github/pull_request_template.md` with sections for Spec, What changed, How I tested it, What I checked by hand.

## Out of scope

- Adding tests, linters, or CI (later phases).
- Changing any application code.

## Acceptance criteria

- `CLAUDE.md` exists and accurately describes the repo.
- `docs/specs/000-template.md` exists with the standard sections.
- `.github/pull_request_template.md` exists with the required sections.

## Test plan

- Read each file and confirm it matches the requirements.

## Notes

None.

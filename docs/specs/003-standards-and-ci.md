# 003 Standards and CI

## Goal

Add linting, formatting, CI, and clean up project config files to match the project standards.

## Context

The repo has no linter, no formatter config, no CI, and the `.gitignore` is a Bitbucket template with irrelevant entries. The standards call for ruff (lint + format), pytest, a `pyproject.toml`, and a GitHub Actions CI workflow.

## Scope

- Add ruff config to `pyproject.toml` for linting and formatting.
- Apply ruff formatting in its own commit (pure formatting, no behavior changes).
- Fix or suppress all ruff lint errors in a separate commit.
- Add `.github/workflows/ci.yml` that runs ruff check, ruff format check, and pytest on push/PR to main and dev.
- Replace `.gitignore` with a Python-focused one covering `.env`, `secrets/`, `__pycache__/`, `.pytest_cache/`, etc.
- Add `.env.example` listing all variables the code reads with placeholder values.

## Out of scope

- Changing application behavior.
- Baseline tests must pass unchanged after this phase.

## Acceptance criteria

- `ruff check .` passes with no errors.
- `ruff format --check .` passes with no errors.
- `pytest` still passes (all 31 baseline tests).
- `.github/workflows/ci.yml` exists and is valid.
- `.gitignore` is clean and Python-focused.
- `.env.example` lists all three environment variables with placeholders.

## Test plan

- Run `ruff check .`, `ruff format --check .`, and `pytest -v` locally.
- After push, confirm CI passes on GitHub.

## Notes

None.

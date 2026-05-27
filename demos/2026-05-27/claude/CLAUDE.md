# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This is a demo workspace for the **Claude Code** module of the "Code Development with AI Assistants" course by Data For Science. It sits within a larger repo (`DataForScience/CodeAI`) that also contains parallel demos for Cursor and Windsurf. The demo instructions are in `Demo_Instructions.md` at the repo root.

Demos in this directory are live-coded during the course session. They typically follow a pattern: generate code from a prompt, iterate on it, then test. Prompt files (`prompt*.txt`) capture the prompts used during the session for reference.

## Commands

This project uses `uv` for dependency management (Python 3.14):

```bash
uv sync                       # install dependencies
uv run python <script>.py     # run a script
uv run pytest                 # run tests (if any)
```

The parent directory (`demos/2026-05-27/`) has its own `pyproject.toml` and `uv.lock`; this subdirectory may get its own as the demo progresses.

## Architecture

The workspace starts empty and is built up during the live demo. Typical demo artifacts include:

- **Web scraper** — `scraper.py` using `requests` + `beautifulsoup4`, with CLI interface and auth support
- **Flask REST API** — `app.py`, `models.py`, `schemas.py`, `config.py` with SQLAlchemy + marshmallow
- **Auth module** — `auth/jwt_handler.py` and `auth/middleware.py` for JWT authentication
- **Prompt files** — `prompt*.txt` files recording the prompts used in each demo step

Sibling demo directories (`../cursor/`, `../windsurf/`) contain the same exercises implemented with those tools, useful for comparison.

## Conventions

- Flask apps use SQLite (`instance/users.db`) for persistence
- HTML templates go in `templates/` using Jinja2 with a `base.html` layout
- The shared `data/iris.csv` at the repo root is available for data-oriented demos
- A custom matplotlib style (`d4sci.mplstyle`) is at the repo root if plotting is needed

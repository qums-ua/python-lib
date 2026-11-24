# Contributing

## Development Setup

1. Clone the repo and sync dependencies:

   ```bash
   git clone https://github.com/qums-ua/qums-fetch.git
   cd qums-fetch
   uv sync
   ```

2. Run linters and offline tests before pushing:

   ```bash
   uv run ruff check
   uv run ruff format --check
   uv run ty check
   uv run pytest
   ```

3. To run the live tests, copy `.env.example` to `.env`, fill in your QUMS credentials, and run `uv run pytest tests/integration`. The login-page test does not need credentials; authenticated tests skip when credentials are missing.

## What to work on

Check [TODO.md](TODO.md) for open tasks and API coverage.

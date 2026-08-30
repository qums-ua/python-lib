# Contributing

## Development Setup

1. Clone the repo and sync dependencies:

   ```bash
   git clone https://github.com/user/qums-fetch.git
   cd qums-fetch
   uv sync
   ```

2. Create a `.env` file with your QUMS credentials (see [README.md](README.md)).

3. Run linters and tests before pushing:

   ```bash
   uv run ruff check
   uv run ruff format --check
   uv run pytest
   ```

## What to work on

Check [TODO.md](TODO.md) for open tasks and API coverage.

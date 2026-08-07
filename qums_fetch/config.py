"""Loads credentials from .env. Keep this the single source of truth for
config so nothing else in the codebase touches os.environ directly."""

import os

from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("QUMS_USERNAME")
PASSWORD = os.getenv("QUMS_PASSWORD")


def validate() -> None:
    missing = [
        name
        for name, value in [
            ("QUMS_USERNAME", USERNAME),
            ("QUMS_PASSWORD", PASSWORD),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required .env values: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

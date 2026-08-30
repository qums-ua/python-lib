"""Simple smoke test: instantiate client and fetch dashboard APIs."""

import logging
import os
import sys

from dotenv import load_dotenv

from src.qums_fetch import Client, Error

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    # Load credentials
    load_dotenv()
    username = os.getenv("QUMS_USERNAME")
    password = os.getenv("QUMS_PASSWORD")

    # Log user in
    try:
        client = Client(username, password)
        logger.info("Logged in successfully as %s.", username)
    except Error as e:
        logger.error("Login failed: %s", e)
        return 1

    # Fetch student details
    print(client.student_details)

    # Fetch tile data
    print(client.tile_data)

    # Fetch today's attendance
    print(client.today_attendance)

    # Fetch monthly attendance
    print(client.month_attendance)

    # Fetch semester attendance
    print(client.sem_attendance)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Confirms the login flow (session, CSRF token, form submission) and OCR
captcha solving work end to end. Loads credentials from .env, solves the
captcha in memory, and prints the fetched dashboard data.
"""

import logging
import os
import sys

from dotenv import load_dotenv

from qums_fetch import Client, CaptchaSolver, Error

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    # Load credentials
    load_dotenv()
    username = os.getenv("QUMS_USERNAME")
    password = os.getenv("QUMS_PASSWORD")

    # Create client instance
    client = Client(username, password)

    # Load the login page and extract captcha image
    challenge = client.fetch_login_challenge()

    try:
        solver = CaptchaSolver(challenge.image_bytes)
        captcha_value = solver.guess()

        # Submit solved captcha
        client.submit_login(challenge, captcha_value)
    except Error as e:
        logger.error("Login failed: %s", e)
        return 1

    logger.info("Logged in successfully as %s.", username)

    # Fetch student deatails
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

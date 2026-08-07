"""
Confirms the login flow (session, CSRF token, form submission) works
end-to-end before we wire up OCR. Loads credentials from .env, saves
the captcha image to disk so you can open and read it, then prompts
you to type the code.
"""

import logging
import sys

from qums_fetch import config, Client, Error

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CAPTCHA_DUMP_PATH = "captcha_debug.png"
PROFILE_DUMP_PATH = "profile_debug.png"


def main() -> int:
    config.validate()

    client = Client(config.USERNAME, config.PASSWORD)

    # Load the login page and extract captcha image
    try:
        challenge = client.fetch_login_challenge()
    except Error as e:
        logger.error("Failed to load login page: %s", e)
        return 1

    # Save captch image to disk
    with open(CAPTCHA_DUMP_PATH, "wb") as f:
        f.write(challenge.image_bytes)
    logger.info(
        "Captcha image saved to '%s' — open it and read the code.", CAPTCHA_DUMP_PATH
    )

    captcha_value = input("> Enter captcha text: ").strip()

    # Submit solved captcha
    try:
        client.submit_login(challenge, captcha_value)
    except Error as e:
        logger.error("Login failed: %s", e)
        return 1

    logger.info("Logged in successfully as %s.", config.USERNAME)

    # Fetch student deatails
    print(client.get_student_details())

    # Fetch today's attendance
    print(client.get_today_attendance())

    return 0


if __name__ == "__main__":
    sys.exit(main())

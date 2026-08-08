"""
Confirms the login flow (session, CSRF token, form submission) works
end-to-end before we wire up OCR. Loads credentials from .env, saves
the captcha image to disk so you can open and read it, then prompts
you to type the code.
"""

import logging
import sys

from qums_fetch import config, Client, CaptchaSolver, Error

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CAPTCHA_DUMP_PATH = "captcha_debug.png"
CAPTCHA_BW_DUMP_PATH = "captcha_bw.png"
PROFILE_DUMP_PATH = "profile_debug.png"


def main() -> int:
    config.validate()

    client = Client(config.USERNAME, config.PASSWORD)

    # Load the login page and extract captcha image
    challenge = client.fetch_login_challenge()

    # Save captch image to disk
    with open(CAPTCHA_DUMP_PATH, "wb") as f:
        f.write(challenge.image_bytes)
    logger.info("Captcha image saved to '%s'", CAPTCHA_DUMP_PATH)

    # Solve captcha (OCR or manual)
    solver = CaptchaSolver(challenge.image_bytes, CAPTCHA_BW_DUMP_PATH)
    captcha_value = solver.guess()

    # Submit solved captcha
    try:
        client.submit_login(challenge, captcha_value)
    except Error as e:
        logger.error("Login failed: %s", e)
        return 1

    logger.info("Logged in successfully as %s.", config.USERNAME)

    # Fetch student deatails
    print(client.student_details)

    # Fetch today's attendance
    print(client.today_attendance)

    return 0


if __name__ == "__main__":
    sys.exit(main())

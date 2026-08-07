# qums.py

Small Python client for the QUMS ERP dashboard.

## Quick start

Create a `.env` file with:

```env
QUMS_USERNAME=your_username
QUMS_PASSWORD=your_password
```

Then run the smoke test script:

```bash
uv sync
uv run main.py
```

The script downloads the login captcha, saves it as `captcha_debug.png`, prompts for the captcha text, and then prints student details and today's attendance after login succeeds.

## Usage

```python
from qums_fetch import Client, config

config.validate()
client = Client(config.USERNAME, config.PASSWORD)
challenge = client.fetch_login_challenge()
```

Call `client.submit_login(challenge, captcha_text)` once you have solved the captcha.

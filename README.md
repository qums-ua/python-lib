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

The script downloads the login captcha, runs OCR on it, and then prints student details and today's attendance after login succeeds.

## Usage

```python
from qums_fetch import CaptchaSolver, Client, config

config.validate()
client = Client(config.USERNAME, config.PASSWORD)
challenge = client.fetch_login_challenge()

solver = CaptchaSolver(challenge.image_bytes, "captcha_bw.png")
captcha_value = solver.guess()

client.submit_login(challenge, captcha_value)
```

## Credits

The captcha solving approach in this project is based on [Kyun-UMS](https://github.com/24kaushik/Kyun-UMS) by [24kaushik](https://github.com/24kaushik).

# qums.py

Small Python client for the QUMS ERP dashboard.

## Quick start

Create a `.env` file with:

```env
QUMS_USERNAME=your_username
QUMS_PASSWORD=your_password
```

Then install dependencies:

```bash
uv sync
```

## Usage

```python
from qums_fetch import Client

client = Client(USERNAME, PASSWORD)
print(client.student_details)
print(client.today_attendance)
```

## Credits

The captcha solving approach in this project is based on [Kyun-UMS](https://github.com/24kaushik/Kyun-UMS) by [24kaushik](https://github.com/24kaushik).

# qums.py

Automatically fetch student data from QUMS

## Prerequisites

[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) must be installed on your system for captcha solving:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
scoop install tesseract
```

## Quick start

Create a `.env` file with:

```env
QUMS_USERNAME=your_username
QUMS_PASSWORD=your_password
```

Then install the package:

```bash
pip install qums-fetch
```

## Usage

```python
from qums_fetch import Client

client = Client(USERNAME, PASSWORD)
print(client.student_details)
print(client.today_attendance)
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.
Check [TODO.md](TODO.md) for open tasks and API coverage.

## Credits

The captcha solving approach in this project is based on [Kyun-UMS](https://github.com/24kaushik/Kyun-UMS) by [24kaushik](https://github.com/24kaushik).

# qums-fetch

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

Install the package:

```bash
pip install qums-fetch
```

## Usage

> [!NOTE]
> Captchas are solved with Tesseract by default. To use a different engine, pass `ocr=your_callable` to `Client`. The callable accepts a Pillow image and returns a string.

```python
from qums_fetch import Client

client = Client("your_username", "your_password")
print(client.student.details)
print(client.attendance.today)
```

Data endpoints are grouped under `client.student` (`details`, `tile_data`, and `photo`) and `client.attendance` (`today`, `month`, and `semester`). To migrate from the flat API, use `client.student.get_details()` instead of `client.get_student_details()`, or `client.attendance.get_today()` instead of `client.get_today_attendance()`.

Data properties fetch on first access and cache the result. Call the corresponding `get_*` method to refresh and return the data. The photo is loaded along with the student details.

An explicit month or semester, such as `client.attendance.get_month(month=4)`, returns that period's data without replacing the default property's cache.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.
Check [TODO.md](TODO.md) for open tasks and API coverage.

## Credits

The captcha solving approach in this project is based on [Kyun-UMS](https://github.com/24kaushik/Kyun-UMS) by [24kaushik](https://github.com/24kaushik).

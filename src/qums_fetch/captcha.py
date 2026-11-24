import logging
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import pytesseract
from PIL import Image

from .exceptions import BlankCaptchaError, CaptchaError

logger = logging.getLogger(__name__)


class CaptchaSolver:
    def __init__(
        self,
        image_bytes: bytes,
        img_path: str | None = None,
        ocr: Callable[[Image.Image], str] | None = None,
    ):
        self.psm: int = 7
        self.allowed_chars: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.threshold: int = 128
        self.bg_frac: float = 0.001
        self.image_bytes: bytes = image_bytes
        self.ocr: Callable[[Image.Image], str] | None = ocr
        self.img_dump_path: Path | None = Path(img_path) if img_path else None
        self.bw_dump_path: Path | None = (
            self.img_dump_path.with_name(f"bw_{self.img_dump_path.name}")
            if self.img_dump_path
            else None
        )

    @property
    def config(self) -> str:
        return f"--psm {self.psm} -c tessedit_char_whitelist={self.allowed_chars}"

    def _preprocess(self, image_bytes: bytes) -> Image.Image:
        with Image.open(BytesIO(image_bytes)) as image:
            return image.convert("L").point(
                lambda pixel: 255 if pixel > self.threshold else 0
            )

    def _looks_blank(self, bw_image: Image.Image) -> bool:
        histogram = bw_image.histogram()
        total_pixels = bw_image.width * bw_image.height
        if total_pixels == 0:
            return True
        dark_fraction = histogram[0] / total_pixels
        non_background_fraction = min(dark_fraction, 1 - dark_fraction)
        return non_background_fraction < self.bg_frac

    def _solve_captcha(self) -> str:
        if self.img_dump_path:
            self.img_dump_path.parent.mkdir(parents=True, exist_ok=True)
            self.img_dump_path.write_bytes(self.image_bytes)
            logger.info("Saved captcha image to '%s'", self.img_dump_path)

        bw = self._preprocess(self.image_bytes)

        if self.bw_dump_path:
            bw.save(self.bw_dump_path)
            logger.info("Saved preprocessed captcha to '%s'", self.bw_dump_path)

        if self._looks_blank(bw):
            raise BlankCaptchaError(
                "Captcha image appears blank/placeholder after thresholding — "
                "skipping OCR. Fetch a fresh challenge and try again."
            )

        if self.ocr is not None:
            text = self.ocr(bw)
        else:
            text = pytesseract.image_to_string(bw, config=self.config)

        return text.strip()

    def guess(self) -> str:
        try:
            return self._solve_captcha()
        except BlankCaptchaError:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise CaptchaError("Could not solve captcha.") from e

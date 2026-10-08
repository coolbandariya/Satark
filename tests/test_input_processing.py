"""Regression tests for bounded upload preprocessing."""

import unittest
from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from input_processing import (
    MAX_IMAGE_BYTES,
    MAX_PDF_BYTES,
    extract_pdf_text,
    image_to_data_url,
)


class InputProcessingTests(unittest.TestCase):
    def test_invalid_image_has_user_facing_error(self):
        upload = BytesIO(b"not an image")
        upload.name = "bad.png"
        with self.assertRaisesRegex(ValueError, "could not read this image"):
            image_to_data_url(upload)

    def test_oversized_image_is_rejected_before_decode(self):
        upload = SimpleNamespace(size=MAX_IMAGE_BYTES + 1, name="large.png")
        with self.assertRaisesRegex(ValueError, "10 MB processing limit"):
            image_to_data_url(upload)

    def test_oversized_pdf_is_rejected_before_parse(self):
        upload = SimpleNamespace(size=MAX_PDF_BYTES + 1, name="large.pdf")
        with self.assertRaisesRegex(ValueError, "25 MB processing limit"):
            extract_pdf_text(upload)

    def test_valid_image_is_encoded(self):
        buffer = BytesIO()
        Image.new("RGB", (16, 12), "white").save(buffer, format="PNG")
        buffer.seek(0)
        buffer.name = "sample.png"
        value = image_to_data_url(buffer)
        self.assertTrue(value.startswith("data:image/jpeg;base64,"))


if __name__ == "__main__":
    unittest.main()

"""Tests for the extracted video processing helpers."""

import unittest
from io import BytesIO

from PIL import Image

from video_processing import (
    MAX_VIDEO_BYTES,
    MAX_VIDEO_FRAMES,
    pil_frames_to_data_urls,
    transcribe_video_audio,
)


class VideoProcessingTests(unittest.TestCase):
    def test_video_limits_are_positive(self):
        self.assertGreater(MAX_VIDEO_FRAMES, 0)
        self.assertGreater(MAX_VIDEO_BYTES, 0)

    def test_frames_are_encoded_as_jpeg_data_urls(self):
        image = Image.new("RGB", (32, 24), "white")
        urls = pil_frames_to_data_urls([image])
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0].startswith("data:image/jpeg;base64,"))

    def test_empty_frames_return_empty_list(self):
        self.assertEqual(pil_frames_to_data_urls([]), [])

    def test_audio_transcription_gracefully_handles_missing_cv2(self):
        upload = BytesIO(b"not a video")
        upload.name = "sample.mp4"
        with unittest.mock.patch("video_processing._video_dependencies_available", return_value=False):
            self.assertEqual(transcribe_video_audio(upload, object()), "")


if __name__ == "__main__":
    unittest.main()

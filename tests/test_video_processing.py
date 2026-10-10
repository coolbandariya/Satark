"""Tests for the extracted video processing helpers."""

import unittest
from io import BytesIO
from unittest.mock import patch, Mock

from PIL import Image

from config import MAX_UPLOAD_BYTES
from video_processing import (
    MAX_VIDEO_BYTES,
    MAX_VIDEO_FRAMES,
    extract_video_frames,
    pil_frames_to_data_urls,
    transcribe_video_audio,
)


class VideoProcessingTests(unittest.TestCase):
    def test_video_limits_are_positive(self):
        self.assertGreater(MAX_VIDEO_FRAMES, 0)
        self.assertGreater(MAX_VIDEO_BYTES, 0)
        self.assertEqual(MAX_VIDEO_BYTES, MAX_UPLOAD_BYTES)
        self.assertLessEqual(MAX_VIDEO_BYTES, 50 * 1024 * 1024)

    def test_invalid_max_frames_is_rejected_before_opencv_loading(self):
        upload = BytesIO(b"not a video")
        upload.name = "sample.mp4"
        with patch.dict("sys.modules", {"cv2": None}):
            with self.assertRaises(ValueError):
                extract_video_frames(upload, max_frames=0)

    def test_frames_are_encoded_as_jpeg_data_urls(self):
        image = Image.new("RGB", (32, 24), "white")
        urls = pil_frames_to_data_urls([image])
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0].startswith("data:image/jpeg;base64,"))

    def test_empty_frames_return_empty_list(self):
        self.assertEqual(pil_frames_to_data_urls([]), [])

    def test_audio_transcription_gracefully_handles_missing_client(self):
        upload = BytesIO(b"not a video")
        upload.name = "sample.mp4"
        self.assertEqual(transcribe_video_audio(upload, None), "")

    def test_audio_transcription_gracefully_handles_missing_ffmpeg(self):
        upload = BytesIO(b"not a video")
        upload.name = "sample.mp4"
        with patch("video_processing.shutil.which", return_value=None):
            self.assertEqual(transcribe_video_audio(upload, Mock()), "")

    def test_audio_transcription_gracefully_handles_ffmpeg_failure(self):
        upload = BytesIO(b"not a video")
        upload.name = "sample.mp4"
        failed = Mock(returncode=1)
        with patch("video_processing.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("video_processing.subprocess.run", return_value=failed):
            self.assertEqual(transcribe_video_audio(upload, Mock()), "")


if __name__ == "__main__":
    unittest.main()

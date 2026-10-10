"""Tests for provider-secret lookup in Streamlit deployments."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ui import navigation


class ConfiguredGroqApiKeyTests(unittest.TestCase):
    def test_streamlit_secret_takes_precedence_over_environment(self):
        fake_streamlit = SimpleNamespace(secrets={"GROQ_API_KEY": " streamlit-secret "})
        with patch.object(navigation, "st", fake_streamlit), patch.dict(
            os.environ, {"GROQ_API_KEY": "environment-secret"}
        ):
            self.assertEqual(navigation.configured_groq_api_key(), "streamlit-secret")

    def test_environment_variable_is_used_when_streamlit_secret_is_missing(self):
        fake_streamlit = SimpleNamespace(secrets={})
        with patch.object(navigation, "st", fake_streamlit), patch.dict(
            os.environ, {"GROQ_API_KEY": " environment-secret "}
        ):
            self.assertEqual(navigation.configured_groq_api_key(), "environment-secret")

    def test_missing_streamlit_secrets_falls_back_to_environment(self):
        class MissingSecrets:
            def get(self, *_args, **_kwargs):
                raise RuntimeError("secrets are not configured")

        fake_streamlit = SimpleNamespace(secrets=MissingSecrets())
        with patch.object(navigation, "st", fake_streamlit), patch.dict(
            os.environ, {"GROQ_API_KEY": "environment-secret"}
        ):
            self.assertEqual(navigation.configured_groq_api_key(), "environment-secret")

    def test_missing_key_returns_empty_string(self):
        fake_streamlit = SimpleNamespace(secrets={})
        with patch.object(navigation, "st", fake_streamlit), patch.dict(
            os.environ, {}, clear=True
        ):
            self.assertEqual(navigation.configured_groq_api_key(), "")


if __name__ == "__main__":
    unittest.main()

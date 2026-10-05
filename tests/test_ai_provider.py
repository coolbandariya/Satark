"""Tests for Groq provider/model-selection helpers."""

import unittest
from unittest.mock import Mock, patch

from ai_provider import (
    TEXT_MODEL_PREFERENCES,
    VISION_MODEL_PREFERENCES,
    choose_model,
    discover_models,
    get_client,
)


class ProviderHelperTests(unittest.TestCase):
    def test_preferences_are_non_empty(self):
        self.assertTrue(TEXT_MODEL_PREFERENCES)
        self.assertTrue(VISION_MODEL_PREFERENCES)

    def test_choose_model_prefers_first_available_preference(self):
        self.assertEqual(
            choose_model({TEXT_MODEL_PREFERENCES[1], TEXT_MODEL_PREFERENCES[0]}, TEXT_MODEL_PREFERENCES),
            TEXT_MODEL_PREFERENCES[0],
        )

    def test_choose_model_uses_first_preference_when_discovery_is_empty(self):
        self.assertEqual(choose_model(set(), TEXT_MODEL_PREFERENCES), TEXT_MODEL_PREFERENCES[0])

    def test_choose_model_returns_none_when_key_has_no_supported_model(self):
        self.assertIsNone(choose_model({"unrelated-model"}, TEXT_MODEL_PREFERENCES))

    def test_discover_models_supports_object_and_dict_items(self):
        first = Mock(id="model-a")
        listing = Mock(data=[first, {"id": "model-b"}, {"name": "ignored"}])
        client = Mock()
        client.models.list.return_value = listing
        self.assertEqual(discover_models(client), {"model-a", "model-b"})

    def test_discover_models_fails_closed_on_provider_error(self):
        client = Mock()
        client.models.list.side_effect = RuntimeError("provider unavailable")
        self.assertEqual(discover_models(client), set())

    def test_get_client_does_not_construct_without_a_key(self):
        self.assertIsNone(get_client(""))
        self.assertIsNone(get_client(None))

    @patch("ai_provider.Groq")
    def test_get_client_constructs_with_key(self, groq):
        get_client("test-key")
        groq.assert_called_once_with(api_key="test-key")


if __name__ == "__main__":
    unittest.main()

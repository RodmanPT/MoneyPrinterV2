import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before they are imported
sys.modules["ollama"] = MagicMock()
sys.modules["srt_equalizer"] = MagicMock()
sys.modules["termcolor"] = MagicMock()
sys.modules["schedule"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["prettytable"] = MagicMock()
sys.modules["webdriver_manager"] = MagicMock()
sys.modules["selenium_firefox"] = MagicMock()
sys.modules["selenium"] = MagicMock()
sys.modules["moviepy"] = MagicMock()
sys.modules["yagmail"] = MagicMock()
sys.modules["assemblyai"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["undetected_chromedriver"] = MagicMock()
sys.modules["platformdirs"] = MagicMock()

import pytest
from llm_provider import list_models

@patch("llm_provider.get_ollama_base_url")
@patch("llm_provider.ollama.Client")
def test_list_models_success(mock_client_class, mock_get_url):
    # Setup mocks
    mock_get_url.return_value = "http://localhost:11434"
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock the response from client.list()
    mock_response = MagicMock()
    mock_model_a = MagicMock()
    mock_model_a.model = "llama3:latest"
    mock_model_b = MagicMock()
    mock_model_b.model = "mistral:latest"

    mock_response.models = [mock_model_b, mock_model_a]
    mock_client.list.return_value = mock_response

    # Call the function
    models = list_models()

    # Assertions
    assert models == ["llama3:latest", "mistral:latest"]
    mock_client_class.assert_called_once_with(host="http://localhost:11434")
    mock_client.list.assert_called_once()

@patch("llm_provider.get_ollama_base_url")
@patch("llm_provider.ollama.Client")
def test_list_models_empty(mock_client_class, mock_get_url):
    # Setup mocks
    mock_get_url.return_value = "http://localhost:11434"
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    # Mock empty response
    mock_response = MagicMock()
    mock_response.models = []
    mock_client.list.return_value = mock_response

    # Call the function
    models = list_models()

    # Assertions
    assert models == []
    mock_client.list.assert_called_once()

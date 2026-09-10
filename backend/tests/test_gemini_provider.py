import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm import GeminiLLMProvider, get_llm_provider, MockLLMProvider
from app.core.config import settings


@pytest.mark.asyncio
async def test_gemini_provider_initialization():
    provider = GeminiLLMProvider(api_key="test_api_key", model="gemini-2.5-flash")
    assert provider.api_key == "test_api_key"
    assert provider.model == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_gemini_provider_missing_key_raises():
    provider = GeminiLLMProvider(api_key="", model="gemini-2.5-flash")
    with pytest.raises(ValueError, match="Gemini API key is missing"):
        await provider.generate_response("Hello")


@pytest.mark.asyncio
async def test_gemini_provider_sdk_generate_response():
    provider = GeminiLLMProvider(api_key="valid_test_key", model="gemini-2.5-flash")
    # Mock client and aio.models.generate_content
    mock_response = MagicMock()
    mock_response.text = "This is a grounded answer from Gemini."

    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    res = await provider.generate_response(
        prompt="What is Subramanya's employee ID?",
        system_prompt="Answer strictly from context."
    )
    assert res == "This is a grounded answer from Gemini."
    provider._client.aio.models.generate_content.assert_awaited_once()


def test_get_llm_provider_fallback_when_gemini_key_missing():
    original_provider = settings.LLM_PROVIDER
    original_key = settings.GEMINI_API_KEY
    try:
        settings.LLM_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = ""
        provider = get_llm_provider()
        # Gracefully falls back to MockLLMProvider when key is unset
        assert isinstance(provider, MockLLMProvider)
    finally:
        settings.LLM_PROVIDER = original_provider
        settings.GEMINI_API_KEY = original_key


def test_get_llm_provider_resolves_gemini_when_key_present():
    original_provider = settings.LLM_PROVIDER
    original_key = settings.GEMINI_API_KEY
    original_model = settings.GEMINI_MODEL
    try:
        settings.LLM_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = "test_actual_key"
        settings.GEMINI_MODEL = "gemini-2.5-flash"
        provider = get_llm_provider()
        assert isinstance(provider, GeminiLLMProvider)
        assert provider.api_key == "test_actual_key"
        assert provider.model == "gemini-2.5-flash"
    finally:
        settings.LLM_PROVIDER = original_provider
        settings.GEMINI_API_KEY = original_key
        settings.GEMINI_MODEL = original_model

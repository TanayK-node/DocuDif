import os
from typing import Optional
from llm_providers.base import BaseLLMProvider
from llm_providers.fallback_provider import DeterministicFallbackProvider
from llm_providers.gemini_provider import GeminiProvider

def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory to instantiate the appropriate LLM or rule provider.
    Lightweight production setup: supports Gemini API and Deterministic Rule Engine.
    """
    chosen = (provider_name or os.getenv("DOCUDIFF_LLM_PROVIDER", "")).lower()

    if chosen == "gemini":
        return GeminiProvider()
    elif chosen == "deterministic" or chosen == "qwen":
        return DeterministicFallbackProvider()

    # Default: if GEMINI_API_KEY is configured in .env, use Gemini, else deterministic
    if os.getenv("GEMINI_API_KEY"):
        return GeminiProvider()

    return DeterministicFallbackProvider()


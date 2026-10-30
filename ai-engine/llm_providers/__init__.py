import os
from typing import Optional
from llm_providers.base import BaseLLMProvider
from llm_providers.fallback_provider import DeterministicFallbackProvider
from llm_providers.gemini_provider import GeminiProvider
from llm_providers.qwen_provider import QwenProvider

def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory to instantiate the appropriate LLM or rule provider.
    Priority:
    1. Explicit provider_name if passed ('gemini', 'qwen', 'deterministic')
    2. Environment variable DOCUDIFF_LLM_PROVIDER
    3. If GEMINI_API_KEY is present and DOCUDIFF_LLM_PROVIDER not forced, Gemini can be used
    4. Otherwise fallback to Deterministic / Qwen
    """
    chosen = provider_name or os.getenv("DOCUDIFF_LLM_PROVIDER", "").lower()

    if chosen == "gemini":
        return GeminiProvider()
    elif chosen == "qwen":
        return QwenProvider()
    elif chosen == "deterministic":
        return DeterministicFallbackProvider()

    # Default heuristic: if GEMINI_API_KEY is set in environment, use Gemini, else deterministic fallback
    if os.getenv("GEMINI_API_KEY"):
        return GeminiProvider()

    return DeterministicFallbackProvider()


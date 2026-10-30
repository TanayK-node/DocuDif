import os
import json
import time
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    # Look for .env in current directory or project root
    root_env = Path(__file__).resolve().parent.parent.parent / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env)
    else:
        load_dotenv()
except ImportError:
    pass

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas import LLMAnalysisOutput, RuleFlag
from llm_providers.base import BaseLLMProvider
from llm_providers.json_repair import extract_and_parse_json, validate_or_fallback_output
from llm_providers.fallback_provider import DeterministicFallbackProvider

BATCH_SYSTEM_PROMPT = """You are DocuDiff AI, an expert document change and policy difference analyzer.
You will be provided a list of document clause edits with their OLD text, NEW text, change type, and pre-detected deterministic rule signals.

For EACH item, produce an objective analysis adhering strictly to this schema:
[
  {
    "id": <integer matching the input item id>,
    "semantic_class": "material_change | wording_only | addition | removal",
    "category": "Wording-only / no material meaning change | Meaning or obligation changed | Numeric, date or duration changed | Negation or exception changed | Permission, role or access-scope changed | Condition, approval or process changed | Added requirement / removed requirement | Uncertain — human review required",
    "explanation": "Clear, concise sentence explaining exactly what changed.",
    "implication": "Practical operational or legal implication.",
    "confidence": 0.85,
    "requires_human_review": true
  }
]
Respond ONLY with a valid JSON array matching the above structure. Do not include markdown commentary outside the JSON array.
"""

# Default to fast, low-latency, rate-limit friendly Flash Lite models
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self.fallback = DeterministicFallbackProvider()
        self._model = None
        self._init_attempted = False

    def _ensure_client(self):
        if self._init_attempted:
            return self._model is not None

        self._init_attempted = True
        if not self.api_key:
            return False

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            return True
        except Exception:
            self._model = None
            return False

    def get_provider_name(self) -> str:
        return f"Gemini API ({self.model_name})"

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Calls Gemini API with exponential backoff on rate limits (429 / ResourceExhausted)."""
        import google.generativeai as genai

        for attempt in range(max_retries + 1):
            try:
                response = self._model.generate_content(prompt)
                if response and response.text:
                    return response.text
                return None
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str
                is_model_not_found = "404" in err_str or "not found" in err_str or "models/" in err_str

                # If the specific model name (e.g. experimental/custom) was not found, fallback to standard flash
                if is_model_not_found and self.model_name != "gemini-1.5-flash":
                    try:
                        self.model_name = "gemini-1.5-flash"
                        self._model = genai.GenerativeModel(
                            model_name=self.model_name,
                            generation_config={"response_mime_type": "application/json"}
                        )
                        continue
                    except Exception:
                        pass

                if is_rate_limit and attempt < max_retries:
                    sleep_time = (attempt + 1) * 3
                    time.sleep(sleep_time)
                    continue

                # Unrecoverable or out of retries
                raise e

    def analyze_changes_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[LLMAnalysisOutput]:
        """
        Batch processes all changes in a single API call to completely prevent rate limiting.
        """
        if not items:
            return []

        # If API key not set or client unavailable, immediately return deterministic results
        if not self._ensure_client():
            return [
                self.fallback.analyze_change(
                    it.get("old_text", ""),
                    it.get("new_text", ""),
                    it.get("rule_flags", []),
                    it.get("change_type", "modified")
                )
                for it in items
            ]

        # Chunk items into batches of up to 15 to stay well within token limits and latency budgets
        BATCH_SIZE = 15
        results: List[LLMAnalysisOutput] = []

        for batch_idx in range(0, len(items), BATCH_SIZE):
            batch_slice = items[batch_idx : batch_idx + BATCH_SIZE]

            # Format batch request payload
            batch_payload = []
            for idx, it in enumerate(batch_slice):
                rule_desc = [f"{f.rule_id}: {f.description}" for f in it.get("rule_flags", [])]
                batch_payload.append({
                    "id": idx,
                    "change_type": it.get("change_type", "modified"),
                    "old_text": it.get("old_text", ""),
                    "new_text": it.get("new_text", ""),
                    "rule_flags": rule_desc
                })

            prompt = (
                f"{BATCH_SYSTEM_PROMPT}\n\n"
                f"CHANGES TO ANALYZE (JSON):\n"
                f"{json.dumps(batch_payload, indent=2)}\n\n"
                f"JSON OUTPUT ARRAY:"
            )

            try:
                raw_response = self._call_gemini_with_retry(prompt)
                parsed_list = extract_and_parse_json(raw_response or "")

                # Parse JSON array
                if isinstance(parsed_list, list):
                    parsed_by_id = {
                        item.get("id"): item for item in parsed_list if isinstance(item, dict) and "id" in item
                    }
                else:
                    parsed_by_id = {}

                for idx, it in enumerate(batch_slice):
                    p_item = parsed_by_id.get(idx)
                    flags = it.get("rule_flags", [])
                    default_cat = flags[0].category if flags else "Meaning or obligation changed"

                    if p_item:
                        out = validate_or_fallback_output(p_item, default_category=default_cat)
                    else:
                        out = self.fallback.analyze_change(
                            it.get("old_text", ""),
                            it.get("new_text", ""),
                            flags,
                            it.get("change_type", "modified")
                        )
                        out.llm_error = "Item omitted in batch response; fell back to rule analyzer."
                    results.append(out)

            except Exception as e:
                # Rate limit or API error fallback: guarantee zero request crashes
                for it in batch_slice:
                    fb = self.fallback.analyze_change(
                        it.get("old_text", ""),
                        it.get("new_text", ""),
                        it.get("rule_flags", []),
                        it.get("change_type", "modified")
                    )
                    fb.llm_error = f"Gemini API rate limit/error: {str(e)[:160]}; safely fell back to rule analyzer."
                    results.append(fb)

            # Polite pause if multiple batches are needed
            if batch_idx + BATCH_SIZE < len(items):
                time.sleep(1.5)

        return results

    def analyze_change(
        self,
        old_text: str,
        new_text: str,
        rule_flags: List[RuleFlag],
        change_type: str = "modified"
    ) -> LLMAnalysisOutput:
        """Single-item wrapper using the batch pipeline."""
        res = self.analyze_changes_batch([{
            "old_text": old_text,
            "new_text": new_text,
            "rule_flags": rule_flags,
            "change_type": change_type
        }])
        return res[0]

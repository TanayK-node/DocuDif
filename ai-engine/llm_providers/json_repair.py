import json
import re
from typing import Optional, Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas import LLMAnalysisOutput

ALLOWED_CATEGORIES = [
    "Wording-only / no material meaning change",
    "Meaning or obligation changed",
    "Numeric, date or duration changed",
    "Negation or exception changed",
    "Permission, role or access-scope changed",
    "Condition, approval or process changed",
    "Added requirement / removed requirement",
    "Uncertain — human review required"
]

def extract_and_parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON object from arbitrary LLM response text,
    tolerating code fences, conversational prose, and minor syntax defects.
    """
    if not raw_text:
        return None

    cleaned = raw_text.strip()

    # 1. Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # 2. Extract first matching outer balanced JSON object {...}
    match = re.search(r"(\{[\s\S]*\})", cleaned)
    if not match:
        return None

    json_candidate = match.group(1)

    # First try direct parse
    try:
        return json.loads(json_candidate)
    except Exception:
        pass

    # 3. Clean common LLM formatting issues
    repaired = json_candidate
    # Remove trailing commas before } or ]
    repaired = re.sub(r",\s*([\}\]])", r"\1", repaired)
    # Replace single quotes around keys/values with double quotes
    repaired = re.sub(r"\'([^\'\"]+)\'\s*:", r'"\1":', repaired)
    repaired = re.sub(r":\s*\'([^\'\"]+)\'", r': "\1"', repaired)

    try:
        return json.loads(repaired)
    except Exception:
        return None

def validate_or_fallback_output(
    parsed_data: Optional[Dict[str, Any]],
    default_category: str = "Uncertain — human review required",
    default_explanation: str = "Automated analysis completed with deterministic heuristics.",
    error_msg: Optional[str] = None
) -> LLMAnalysisOutput:
    """Validates raw dictionary against LLMAnalysisOutput schema with graceful defaults."""
    if not parsed_data:
        return LLMAnalysisOutput(
            semantic_class="uncertain",
            category=default_category,
            explanation=default_explanation,
            implication="Review the highlighted textual differences to verify practical impact.",
            confidence=0.5,
            requires_human_review=True,
            llm_error=error_msg
        )

    # Validate category against standard specification categories
    category = parsed_data.get("category", "")
    if category not in ALLOWED_CATEGORIES:
        # Match closest category keyword
        cat_lower = str(category).lower()
        if "numeric" in cat_lower or "date" in cat_lower or "duration" in cat_lower:
            category = "Numeric, date or duration changed"
        elif "modal" in cat_lower or "obligation" in cat_lower or "meaning" in cat_lower:
            category = "Meaning or obligation changed"
        elif "negation" in cat_lower or "exception" in cat_lower:
            category = "Negation or exception changed"
        elif "permission" in cat_lower or "role" in cat_lower or "access" in cat_lower or "scope" in cat_lower:
            category = "Permission, role or access-scope changed"
        elif "approval" in cat_lower or "condition" in cat_lower or "process" in cat_lower:
            category = "Condition, approval or process changed"
        elif "wording" in cat_lower:
            category = "Wording-only / no material meaning change"
        elif "added" in cat_lower or "removed" in cat_lower:
            category = "Added requirement / removed requirement"
        else:
            category = default_category

    semantic_class = parsed_data.get("semantic_class", "material_change")
    explanation = str(parsed_data.get("explanation", default_explanation)).strip()[:1000]
    implication = str(parsed_data.get("implication", "Human review recommended.")).strip()[:1000]

    try:
        confidence = float(parsed_data.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    requires_human_review = bool(parsed_data.get("requires_human_review", True))

    return LLMAnalysisOutput(
        semantic_class=semantic_class,
        category=category,
        explanation=explanation,
        implication=implication,
        confidence=confidence,
        requires_human_review=requires_human_review,
        llm_error=error_msg
    )


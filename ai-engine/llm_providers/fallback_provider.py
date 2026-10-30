from typing import List, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas import LLMAnalysisOutput, RuleFlag
from llm_providers.base import BaseLLMProvider

class DeterministicFallbackProvider(BaseLLMProvider):
    """
    High-reliability rule-based analyzer that synthesizes deterministic flags
    and diff semantics into structured, transparent explanations.
    """
    def get_provider_name(self) -> str:
        return "Deterministic Rule Engine (Offline/Fallback)"

    def analyze_change(
        self,
        old_text: str,
        new_text: str,
        rule_flags: List[RuleFlag],
        change_type: str = "modified"
    ) -> LLMAnalysisOutput:
        if change_type == "unchanged":
            return LLMAnalysisOutput(
                semantic_class="unchanged",
                category="Wording-only / no material meaning change",
                explanation="The clause is identical in both versions.",
                implication="No operational impact.",
                confidence=1.0,
                requires_human_review=False
            )

        if change_type == "added":
            has_approval = any(f.rule_id == "RULE_APPROVAL_ADDED" for f in rule_flags)
            return LLMAnalysisOutput(
                semantic_class="addition",
                category="Added requirement / removed requirement" if not has_approval else "Condition, approval or process changed",
                explanation=f"New provision introduced: '{new_text}'.",
                implication="Confirm whether this new requirement necessitates procedural or compliance updates.",
                confidence=0.9,
                requires_human_review=True
            )

        if change_type == "removed":
            return LLMAnalysisOutput(
                semantic_class="removal",
                category="Added requirement / removed requirement",
                explanation=f"Clause deleted from new document: '{old_text}'.",
                implication="Verify whether removal was intentional and assess potential loss of governance control.",
                confidence=0.9,
                requires_human_review=True
            )

        # Handle modified
        if rule_flags:
            # Pick highest severity flag as primary category
            primary_flag = rule_flags[0]
            descriptions = [f.description for f in rule_flags]
            full_explanation = " ".join(descriptions)

            implication = "Evaluate the operational and compliance effect of this modification."
            if any("obligation" in f.rule_id.lower() or "modal" in f.rule_id.lower() for f in rule_flags):
                implication = "Mandatory obligations require strict adherence and may affect audit readiness."
            elif any("numeric" in f.rule_id.lower() for f in rule_flags):
                implication = "Numerical limits or timelines have changed; update operational calendars and thresholds."
            elif any("permission" in f.rule_id.lower() for f in rule_flags):
                implication = "Access rights or authorized personnel roles have been expanded or altered."

            return LLMAnalysisOutput(
                semantic_class="material_change",
                category=primary_flag.category,
                explanation=full_explanation,
                implication=implication,
                confidence=0.95,
                requires_human_review=True
            )

        # Wording only modification without rule flags
        return LLMAnalysisOutput(
            semantic_class="wording_only",
            category="Wording-only / no material meaning change",
            explanation="Phrasing changed without altering quantities, modal obligations, or authorized actors.",
            implication="Low risk: likely editorial or stylistic revision.",
            confidence=0.85,
            requires_human_review=False
        )


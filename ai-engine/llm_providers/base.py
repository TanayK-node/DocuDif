from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory to sys.path so schemas can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas import LLMAnalysisOutput, RuleFlag

class BaseLLMProvider(ABC):
    @abstractmethod
    def analyze_change(
        self,
        old_text: str,
        new_text: str,
        rule_flags: List[RuleFlag],
        change_type: str = "modified"
    ) -> LLMAnalysisOutput:
        """
        Analyze the semantic difference between old_text and new_text.
        Returns a validated LLMAnalysisOutput.
        """
        pass

    def analyze_changes_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[LLMAnalysisOutput]:
        """
        Batch analyze multiple changes to conserve API quota and avoid rate-limiting.
        Default implementation calls analyze_change sequentially.
        """
        return [
            self.analyze_change(
                item.get("old_text", ""),
                item.get("new_text", ""),
                item.get("rule_flags", []),
                item.get("change_type", "modified")
            )
            for item in items
        ]

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable identifier of the provider."""
        pass

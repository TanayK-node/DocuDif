import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List
import sys

# Add ai-engine to sys.path
ENGINE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ai-engine"
if str(ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(ENGINE_PATH))

from schemas import ComparisonResult, ChangeRecord
from graph_workflow import run_comparison_pipeline
from core.config import settings

class ComparisonService:
    def __init__(self):
        # In-memory comparison cache keyed by comparison_id
        self._comparisons: Dict[str, ComparisonResult] = {}

    def run_comparison(
        self,
        old_file_path: Path,
        new_file_path: Path,
        provider: Optional[str] = None,
        threshold: Optional[float] = None,
        use_langgraph: Optional[bool] = None
    ) -> ComparisonResult:
        threshold_val = threshold if threshold is not None else settings.DEFAULT_THRESHOLD
        langgraph_val = use_langgraph if use_langgraph is not None else settings.USE_LANGGRAPH
        provider_val = provider or settings.DEFAULT_PROVIDER

        result = run_comparison_pipeline(
            old_file_path=str(old_file_path),
            new_file_path=str(new_file_path),
            provider_name=provider_val,
            threshold=threshold_val,
            use_langgraph=langgraph_val
        )

        cid = result.summary.comparison_id
        self._comparisons[cid] = result
        return result

    def get_comparison(self, comparison_id: str) -> Optional[ComparisonResult]:
        return self._comparisons.get(comparison_id)

    def list_comparisons(self) -> List[Dict]:
        return [
            {
                "comparison_id": r.summary.comparison_id,
                "old_filename": r.summary.old_filename,
                "new_filename": r.summary.new_filename,
                "created_at": r.summary.created_at,
                "total_changes": r.summary.total_changes,
                "model": r.summary.model,
                "duration": r.summary.processing_duration_seconds
            }
            for r in self._comparisons.values()
        ]

    def filter_changes(
        self,
        comparison_id: str,
        change_type: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        include_unchanged: bool = False
    ) -> List[ChangeRecord]:
        res = self.get_comparison(comparison_id)
        if not res:
            return []

        filtered = []
        for c in res.changes:
            if not include_unchanged and c.change_type == "unchanged":
                continue
            if change_type and c.change_type != change_type:
                continue
            if priority and c.priority != priority:
                continue
            if category and c.category != category:
                continue
            if search_query:
                sq = search_query.lower()
                in_text = sq in c.old_text.lower() or sq in c.new_text.lower()
                in_expl = sq in c.explanation.lower() or sq in c.implication.lower()
                if not (in_text or in_expl):
                    continue
            filtered.append(c)

        return filtered

comparison_service = ComparisonService()


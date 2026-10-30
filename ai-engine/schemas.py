from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

ChangeType = Literal["added", "removed", "modified", "unchanged"]
PriorityLevel = Literal["low", "medium", "high", "critical"]

class SourceLocation(BaseModel):
    file_name: str
    page: Optional[int] = None
    paragraph: Optional[int] = None
    sentence_idx: Optional[int] = None
    table: Optional[int] = None
    row: Optional[int] = None
    label: str = ""

    def formatted_label(self) -> str:
        if self.label:
            return self.label
        parts = [self.file_name]
        if self.page is not None:
            parts.append(f"page {self.page}")
        if self.paragraph is not None:
            parts.append(f"para {self.paragraph}")
        if self.sentence_idx is not None:
            parts.append(f"sent {self.sentence_idx}")
        if self.table is not None:
            parts.append(f"table {self.table} row {self.row}")
        return ", ".join(parts)

class RuleFlag(BaseModel):
    rule_id: str
    category: str
    description: str
    severity: PriorityLevel = "medium"
    old_value: Optional[str] = None
    new_value: Optional[str] = None

class TokenDiff(BaseModel):
    operation: Literal["equal", "insert", "delete"]
    text: str

class LLMAnalysisOutput(BaseModel):
    semantic_class: str = "uncertain"
    category: str = "Uncertain — human review required"
    explanation: str = ""
    implication: str = ""
    priority_suggestion: Optional[PriorityLevel] = None
    confidence: float = 0.5
    requires_human_review: bool = True
    llm_error: Optional[str] = None

class ChangeRecord(BaseModel):
    change_id: str
    change_type: ChangeType
    old_text: str = ""
    new_text: str = ""
    old_source: Optional[str] = None
    new_source: Optional[str] = None
    similarity: Optional[float] = None
    match_method: str = "unmatched"  # "exact", "semantic", "unmatched"
    semantic_class: str = "uncertain"
    category: str = "Uncertain — human review required"
    rule_flags: List[RuleFlag] = Field(default_factory=list)
    priority: PriorityLevel = "medium"
    priority_reasons: List[str] = Field(default_factory=list)
    explanation: str = ""
    implication: str = ""
    confidence: float = 0.5
    requires_human_review: bool = True
    analysis_status: str = "completed"  # "completed", "fallback", "error"
    diff_tokens: List[TokenDiff] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ComparisonSummary(BaseModel):
    comparison_id: str
    old_filename: str
    new_filename: str
    created_at: str
    total_changes: int
    added: int
    removed: int
    modified: int
    unchanged: int
    priority_breakdown: Dict[str, int] = Field(default_factory=dict)
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    model: str
    embedding_model: str
    processing_duration_seconds: float = 0.0
    langgraph_used: bool = False

class ComparisonResult(BaseModel):
    summary: ComparisonSummary
    changes: List[ChangeRecord]
    warnings: List[str] = Field(default_factory=list)


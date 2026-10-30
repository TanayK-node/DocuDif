import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict

import numpy as np

from schemas import (
    ComparisonResult, ComparisonSummary, ChangeRecord, RuleFlag,
    SourceLocation, TokenDiff, PriorityLevel
)
from document_loader import extract_document
from normalization import normalize_text, normalize_for_matching
from segmentation import segment_document
from embeddings import compute_embeddings
from alignment import align_units
from diff_engine import compute_token_diff
from rule_analyzer import analyze_rule_differences
from prioritization import compute_priority
from llm_providers import get_llm_provider
from llm_providers.base import BaseLLMProvider

def format_source_label(unit: Dict[str, Any]) -> str:
    """Format human-readable provenance label."""
    parts = [unit.get("source", "")]
    if unit.get("page") is not None:
        parts.append(f"page {unit['page']}")
    if unit.get("paragraph") is not None:
        parts.append(f"para {unit['paragraph']}")
    if unit.get("sentence_idx") is not None:
        parts.append(f"sent {unit['sentence_idx']}")
    if unit.get("table") is not None:
        parts.append(f"table {unit['table']} row {unit.get('row')}")
    return ", ".join([p for p in parts if p])

class PipelineState(TypedDict, total=False):
    old_file_path: str
    new_file_path: str
    old_filename: str
    new_filename: str
    old_records: List[Dict[str, Any]]
    new_records: List[Dict[str, Any]]
    old_units: List[Dict[str, Any]]
    new_units: List[Dict[str, Any]]
    old_embeddings: Any
    new_embeddings: Any
    alignment_results: Dict[str, Any]
    change_records: List[ChangeRecord]
    summary: ComparisonSummary
    warnings: List[str]
    provider_name: str
    threshold: float
    langgraph_used: bool

def node_ingest(state: PipelineState) -> PipelineState:
    old_path = Path(state["old_file_path"])
    new_path = Path(state["new_file_path"])
    state["old_filename"] = old_path.name
    state["new_filename"] = new_path.name
    state["old_records"] = extract_document(old_path)
    state["new_records"] = extract_document(new_path)
    state.setdefault("warnings", [])
    return state

def node_normalize_and_segment(state: PipelineState) -> PipelineState:
    # Normalize records
    for r in state["old_records"]:
        r["text"] = normalize_text(r["text"])
    for r in state["new_records"]:
        r["text"] = normalize_text(r["text"])

    state["old_units"] = segment_document(state["old_records"], "old")
    state["new_units"] = segment_document(state["new_records"], "new")
    return state

def node_embed(state: PipelineState) -> PipelineState:
    old_texts = [u["text"] for u in state["old_units"]]
    new_texts = [u["text"] for u in state["new_units"]]
    state["old_embeddings"] = compute_embeddings(old_texts)
    state["new_embeddings"] = compute_embeddings(new_texts)
    return state

def node_align(state: PipelineState) -> PipelineState:
    threshold = state.get("threshold", 0.65)
    state["alignment_results"] = align_units(
        state["old_units"],
        state["new_units"],
        state["old_embeddings"],
        state["new_embeddings"],
        threshold=threshold
    )
    return state

def node_diff_and_rules(state: PipelineState) -> PipelineState:
    provider: BaseLLMProvider = get_llm_provider(state.get("provider_name"))
    align_res = state["alignment_results"]
    matches = align_res["matches"]
    unmatched_old = align_res["unmatched_old"]
    unmatched_new = align_res["unmatched_new"]

    change_records: List[ChangeRecord] = []
    record_id_counter = 1

    # Stage 1: Collect items to analyze with LLM (skip unchanged items to eliminate rate-limiting)
    items_to_batch: List[Dict[str, Any]] = []

    # Map for modified items
    modified_pairs = []
    for m in matches:
        ou = m["old_unit"]
        nu = m["new_unit"]
        sim = m["similarity"]
        match_method = m["match_method"]
        is_exact = normalize_for_matching(ou["text"]) == normalize_for_matching(nu["text"])

        if is_exact:
            # Deterministic zero-API result for identical text
            priority, priority_reasons = compute_priority("unchanged", [], similarity=sim)
            record = ChangeRecord(
                change_id=f"CHG-{record_id_counter:04d}",
                change_type="unchanged",
                old_text=ou["text"],
                new_text=nu["text"],
                old_source=format_source_label(ou),
                new_source=format_source_label(nu),
                similarity=round(sim, 4),
                match_method=match_method,
                semantic_class="unchanged",
                category="Wording-only / no material meaning change",
                rule_flags=[],
                priority=priority,
                priority_reasons=priority_reasons,
                explanation="The clause is identical in both versions.",
                implication="No operational impact.",
                confidence=1.0,
                requires_human_review=False,
                analysis_status="completed",
                diff_tokens=[]
            )
            change_records.append(record)
            record_id_counter += 1
        else:
            rule_flags = analyze_rule_differences(ou["text"], nu["text"])
            diff_tokens = compute_token_diff(ou["text"], nu["text"])
            item_entry = {
                "change_type": "modified",
                "old_text": ou["text"],
                "new_text": nu["text"],
                "rule_flags": rule_flags,
                "meta": {
                    "old_unit": ou,
                    "new_unit": nu,
                    "sim": sim,
                    "match_method": match_method,
                    "diff_tokens": diff_tokens
                }
            }
            items_to_batch.append(item_entry)

    # Removed items
    for ou in unmatched_old:
        diff_tokens = compute_token_diff(ou["text"], "")
        items_to_batch.append({
            "change_type": "removed",
            "old_text": ou["text"],
            "new_text": "",
            "rule_flags": [],
            "meta": {
                "old_unit": ou,
                "diff_tokens": diff_tokens
            }
        })

    # Added items
    for nu in unmatched_new:
        diff_tokens = compute_token_diff("", nu["text"])
        added_rules = analyze_rule_differences("", nu["text"])
        items_to_batch.append({
            "change_type": "added",
            "old_text": "",
            "new_text": nu["text"],
            "rule_flags": added_rules,
            "meta": {
                "new_unit": nu,
                "diff_tokens": diff_tokens,
                "rule_flags": added_rules
            }
        })

    # Stage 2: Execute single batch LLM call across all changed clauses (preventing rate limit)
    if items_to_batch:
        batch_llm_outputs = provider.analyze_changes_batch(items_to_batch)
    else:
        batch_llm_outputs = []

    # Stage 3: Build ChangeRecord objects from batched outputs
    for it, llm_out in zip(items_to_batch, batch_llm_outputs):
        ctype = it["change_type"]
        meta = it["meta"]
        flags = it["rule_flags"]

        if ctype == "modified":
            sim = meta["sim"]
            priority, priority_reasons = compute_priority(
                change_type="modified",
                rule_flags=flags,
                similarity=sim,
                is_wording_only=(llm_out.semantic_class == "wording_only")
            )
            record = ChangeRecord(
                change_id=f"CHG-{record_id_counter:04d}",
                change_type="modified",
                old_text=it["old_text"],
                new_text=it["new_text"],
                old_source=format_source_label(meta["old_unit"]),
                new_source=format_source_label(meta["new_unit"]),
                similarity=round(sim, 4),
                match_method=meta["match_method"],
                semantic_class=llm_out.semantic_class,
                category=llm_out.category,
                rule_flags=flags,
                priority=priority,
                priority_reasons=priority_reasons,
                explanation=llm_out.explanation,
                implication=llm_out.implication,
                confidence=llm_out.confidence,
                requires_human_review=llm_out.requires_human_review,
                analysis_status="fallback" if llm_out.llm_error else "completed",
                diff_tokens=meta["diff_tokens"],
                warnings=[llm_out.llm_error] if llm_out.llm_error else []
            )
        elif ctype == "removed":
            priority, priority_reasons = compute_priority(
                change_type="removed",
                rule_flags=[],
                similarity=0.0
            )
            record = ChangeRecord(
                change_id=f"CHG-{record_id_counter:04d}",
                change_type="removed",
                old_text=it["old_text"],
                new_text="",
                old_source=format_source_label(meta["old_unit"]),
                new_source="—",
                similarity=None,
                match_method="unmatched",
                semantic_class=llm_out.semantic_class,
                category=llm_out.category,
                rule_flags=[],
                priority=priority,
                priority_reasons=priority_reasons,
                explanation=llm_out.explanation,
                implication=llm_out.implication,
                confidence=0.9,
                requires_human_review=True,
                analysis_status="fallback" if llm_out.llm_error else "completed",
                diff_tokens=meta["diff_tokens"],
                warnings=[llm_out.llm_error] if llm_out.llm_error else []
            )
        else:  # added
            priority, priority_reasons = compute_priority(
                change_type="added",
                rule_flags=flags,
                similarity=0.0
            )
            record = ChangeRecord(
                change_id=f"CHG-{record_id_counter:04d}",
                change_type="added",
                old_text="",
                new_text=it["new_text"],
                old_source="—",
                new_source=format_source_label(meta["new_unit"]),
                similarity=None,
                match_method="unmatched",
                semantic_class=llm_out.semantic_class,
                category=llm_out.category,
                rule_flags=flags,
                priority=priority,
                priority_reasons=priority_reasons,
                explanation=llm_out.explanation,
                implication=llm_out.implication,
                confidence=0.9,
                requires_human_review=True,
                analysis_status="fallback" if llm_out.llm_error else "completed",
                diff_tokens=meta["diff_tokens"],
                warnings=[llm_out.llm_error] if llm_out.llm_error else []
            )

        change_records.append(record)
        record_id_counter += 1

    state["change_records"] = change_records
    return state

def node_report_and_validate(state: PipelineState) -> PipelineState:
    records = state["change_records"]
    added_cnt = sum(1 for r in records if r.change_type == "added")
    removed_cnt = sum(1 for r in records if r.change_type == "removed")
    modified_cnt = sum(1 for r in records if r.change_type == "modified")
    unchanged_cnt = sum(1 for r in records if r.change_type == "unchanged")

    # Priority breakdown for changes only
    active_changes = [r for r in records if r.change_type != "unchanged"]
    priority_breakdown = {
        "critical": sum(1 for r in active_changes if r.priority == "critical"),
        "high": sum(1 for r in active_changes if r.priority == "high"),
        "medium": sum(1 for r in active_changes if r.priority == "medium"),
        "low": sum(1 for r in active_changes if r.priority == "low")
    }

    category_breakdown: Dict[str, int] = {}
    for r in active_changes:
        category_breakdown[r.category] = category_breakdown.get(r.category, 0) + 1

    provider = get_llm_provider(state.get("provider_name"))

    summary = ComparisonSummary(
        comparison_id=str(uuid.uuid4())[:8],
        old_filename=state["old_filename"],
        new_filename=state["new_filename"],
        created_at=datetime.now(timezone.utc).isoformat(),
        total_changes=len(active_changes),
        added=added_cnt,
        removed=removed_cnt,
        modified=modified_cnt,
        unchanged=unchanged_cnt,
        priority_breakdown=priority_breakdown,
        category_breakdown=category_breakdown,
        model=provider.get_provider_name(),
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        processing_duration_seconds=0.0,
        langgraph_used=state.get("langgraph_used", False)
    )
    state["summary"] = summary
    return state

def run_comparison_pipeline(
    old_file_path: str,
    new_file_path: str,
    provider_name: Optional[str] = None,
    threshold: float = 0.65,
    use_langgraph: bool = True
) -> ComparisonResult:
    """
    Executes the complete document comparison pipeline.
    Uses LangGraph if available and enabled, with seamless sequential fallback.
    """
    start_time = time.time()
    state: PipelineState = {
        "old_file_path": str(old_file_path),
        "new_file_path": str(new_file_path),
        "provider_name": provider_name or "",
        "threshold": threshold,
        "warnings": [
            "Priority is an automated review triage suggestion, not formal legal advice.",
            "Confidence scores are heuristic estimates and not statistically calibrated."
        ],
        "langgraph_used": False
    }

    ran_with_langgraph = False
    if use_langgraph:
        try:
            from langgraph.graph import StateGraph, START, END
            workflow = StateGraph(PipelineState)
            workflow.add_node("ingest", node_ingest)
            workflow.add_node("normalize_and_segment", node_normalize_and_segment)
            workflow.add_node("embed", node_embed)
            workflow.add_node("align", node_align)
            workflow.add_node("diff_and_rules", node_diff_and_rules)
            workflow.add_node("report_and_validate", node_report_and_validate)

            workflow.add_edge(START, "ingest")
            workflow.add_edge("ingest", "normalize_and_segment")
            workflow.add_edge("normalize_and_segment", "embed")
            workflow.add_edge("embed", "align")
            workflow.add_edge("align", "diff_and_rules")
            workflow.add_edge("diff_and_rules", "report_and_validate")
            workflow.add_edge("report_and_validate", END)

            app = workflow.compile()
            state = app.invoke(state)
            ran_with_langgraph = True
        except Exception as e:
            # Fall back to sequential execution
            state["warnings"].append(f"LangGraph execution encountered an error: {str(e)}; completed sequentially.")
            ran_with_langgraph = False

    if not ran_with_langgraph:
        state = node_ingest(state)
        state = node_normalize_and_segment(state)
        state = node_embed(state)
        state = node_align(state)
        state = node_diff_and_rules(state)
        state = node_report_and_validate(state)

    duration = round(time.time() - start_time, 2)
    state["summary"].processing_duration_seconds = duration
    state["summary"].langgraph_used = ran_with_langgraph

    return ComparisonResult(
        summary=state["summary"],
        changes=state["change_records"],
        warnings=state["warnings"]
    )


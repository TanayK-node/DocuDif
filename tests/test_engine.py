import sys
from pathlib import Path
import pytest

# Ensure ai-engine is in python path
ENGINE_DIR = Path(__file__).resolve().parent.parent / "ai-engine"
sys.path.insert(0, str(ENGINE_DIR))

from document_loader import extract_document
from segmentation import segment_document
from rule_analyzer import analyze_rule_differences
from prioritization import compute_priority
from llm_providers.json_repair import extract_and_parse_json, validate_or_fallback_output
from graph_workflow import run_comparison_pipeline

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
OLD_POLICY = SAMPLES_DIR / "policy_v1.txt"
NEW_POLICY = SAMPLES_DIR / "policy_v2.txt"

def test_document_extraction():
    old_recs = extract_document(OLD_POLICY)
    new_recs = extract_document(NEW_POLICY)
    assert len(old_recs) == 6, f"Expected 6 lines/paragraphs in old policy, got {len(old_recs)}"
    assert len(new_recs) == 7, f"Expected 7 lines/paragraphs in new policy, got {len(new_recs)}"

def test_segmentation_preserves_clauses():
    old_recs = extract_document(OLD_POLICY)
    old_units = segment_document(old_recs, "old")
    assert len(old_units) == 6, f"Expected 6 granular units in old policy, got {len(old_units)}"

    new_recs = extract_document(NEW_POLICY)
    new_units = segment_document(new_recs, "new")
    assert len(new_units) == 7, f"Expected 7 granular units in new policy, got {len(new_units)}"

def test_rule_detection_numeric_changes():
    # 15 days -> 10 days
    t1_old = "Employees may carry forward up to 15 days of unused leave."
    t1_new = "Employees may carry forward up to 10 days of unused leave."
    flags1 = analyze_rule_differences(t1_old, t1_new)
    assert any("RULE_NUMERIC_CHANGE" in f.rule_id for f in flags1), "Numeric change 15 -> 10 days not detected"

    # 7 days -> 5 days
    t2_old = "A leave request must be submitted at least 7 days before planned travel."
    t2_new = "A leave request must be submitted at least 5 days before planned travel."
    flags2 = analyze_rule_differences(t2_old, t2_new)
    assert any("RULE_NUMERIC_CHANGE" in f.rule_id for f in flags2), "Numeric change 7 -> 5 days not detected"

def test_rule_detection_modal_obligation():
    t_old = "The system should retain access logs for 30 days."
    t_new = "The system must retain access logs for 30 days."
    flags = analyze_rule_differences(t_old, t_new)
    assert any("RULE_MODAL_OBLIGATION_CHANGE" in f.rule_id for f in flags), "Modal shift should -> must not detected"

def test_rule_detection_permission_scope():
    t_old = "Access is permitted for approved administrators only."
    t_new = "Access is permitted for approved administrators and auditors."
    flags = analyze_rule_differences(t_old, t_new)
    assert any("RULE_PERMISSION_SCOPE_CHANGE" in f.rule_id for f in flags), "Permission expansion to auditors not detected"

def test_rule_detection_approval_added():
    t_new = "Emergency access requests require manager approval."
    flags = analyze_rule_differences("", t_new)
    assert any("RULE_APPROVAL_ADDED" in f.rule_id for f in flags), "Manager approval requirement not detected"

def test_llm_json_robustness():
    # Test conversational wrapper + markdown fence
    messy_llm = """Certainly! Here is your analysis:
```json
{
  "semantic_class": "material_change",
  "category": "Numeric, date or duration changed",
  "explanation": "Days changed from 15 to 10.",
  "implication": "Reduces carried forward leave.",
  "confidence": 0.95,
  "requires_human_review": true,
}
```
Hope this is helpful!"""
    parsed = extract_and_parse_json(messy_llm)
    assert parsed is not None
    validated = validate_or_fallback_output(parsed)
    assert validated.semantic_class == "material_change"
    assert validated.category == "Numeric, date or duration changed"
    assert validated.confidence == 0.95

    # Test complete garbage output
    bad_output = "I cannot fulfill this request."
    parsed_bad = extract_and_parse_json(bad_output)
    fallback = validate_or_fallback_output(parsed_bad, error_msg="Simulated bad output")
    assert fallback.requires_human_review is True
    assert fallback.llm_error == "Simulated bad output"

def test_full_regression_pipeline():
    result = run_comparison_pipeline(
        old_file_path=str(OLD_POLICY),
        new_file_path=str(NEW_POLICY),
        provider_name="deterministic",
        use_langgraph=True
    )

    summary = result.summary
    # Out of 7 total units in new, 2 are unchanged (title + medical leave), 4 modified, 1 added
    assert summary.total_changes == 5, f"Expected 5 active changes, got {summary.total_changes}"
    assert summary.added == 1, f"Expected 1 added change, got {summary.added}"
    assert summary.removed == 0, f"Expected 0 removed changes, got {summary.removed}"
    assert summary.modified == 4, f"Expected 4 modified changes, got {summary.modified}"
    assert summary.unchanged == 2, f"Expected 2 unchanged items, got {summary.unchanged}"

    # Verify all 5 known edits exist in records
    changes = [r for r in result.changes if r.change_type != "unchanged"]

    # 1. carry forward 15 -> 10
    cf_change = next((c for c in changes if "15 days" in c.old_text and "10 days" in c.new_text), None)
    assert cf_change is not None, "Carry forward 15 -> 10 change missing"
    assert any("numeric" in f.rule_id.lower() for f in cf_change.rule_flags)
    assert cf_change.priority in ["high", "critical"]

    # 2. notice period 7 -> 5
    np_change = next((c for c in changes if "7 days" in c.old_text and "5 days" in c.new_text), None)
    assert np_change is not None, "Notice period 7 -> 5 change missing"
    assert any("numeric" in f.rule_id.lower() for f in np_change.rule_flags)

    # 3. retention should -> must
    ret_change = next((c for c in changes if "should retain" in c.old_text and "must retain" in c.new_text), None)
    assert ret_change is not None, "Retention should -> must change missing"
    assert any("obligation" in f.rule_id.lower() or "modal" in f.rule_id.lower() for f in ret_change.rule_flags)

    # 4. access only -> and auditors
    acc_change = next((c for c in changes if "administrators only" in c.old_text and "auditors" in c.new_text), None)
    assert acc_change is not None, "Access scope auditors change missing"
    assert any("permission" in f.rule_id.lower() or "scope" in f.rule_id.lower() for f in acc_change.rule_flags)

    # 5. emergency access added
    em_change = next((c for c in changes if "Emergency access" in c.new_text), None)
    assert em_change is not None, "Emergency access added change missing"
    assert em_change.change_type == "added"
    assert em_change.priority in ["high", "critical"]

if __name__ == "__main__":
    pytest.main(["-v", __file__])


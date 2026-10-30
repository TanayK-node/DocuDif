import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add ai-engine to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-engine"))

from normalization import normalize_for_matching
from rule_analyzer import analyze_rule_differences
from prioritization import compute_priority
from llm_providers.fallback_provider import DeterministicFallbackProvider

def evaluate_dataset(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    provider = DeterministicFallbackProvider()

    cases = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(row)

    total = len(cases)
    type_matches = 0
    priority_matches = 0
    category_matches = 0

    confusion_type = defaultdict(lambda: defaultdict(int))
    confusion_priority = defaultdict(lambda: defaultdict(int))

    results = []

    for c in cases:
        case_id = c["case_id"]
        old_text = c["old_text"].strip()
        new_text = c["new_text"].strip()
        gt_type = c["ground_truth_change_type"].strip()
        gt_priority = c["ground_truth_priority"].strip()
        gt_category = c["ground_truth_category"].strip()

        # Determine predicted change type
        if not old_text and new_text:
            pred_type = "added"
        elif old_text and not new_text:
            pred_type = "removed"
        elif normalize_for_matching(old_text) == normalize_for_matching(new_text):
            pred_type = "unchanged"
        else:
            pred_type = "modified"

        # Run rule analyzer
        rules = analyze_rule_differences(old_text, new_text)
        analysis = provider.analyze_change(old_text, new_text, rules, pred_type)
        pred_priority, reasons = compute_priority(
            pred_type,
            rules,
            similarity=1.0 if pred_type == "unchanged" else 0.8,
            is_wording_only=(analysis.semantic_class == "wording_only")
        )
        pred_category = analysis.category

        # Evaluate matches
        type_match = (pred_type == gt_type)
        priority_match = (pred_priority == gt_priority)
        category_match = (pred_category == gt_category)

        if type_match:
            type_matches += 1
        if priority_match:
            priority_matches += 1
        if category_match:
            category_matches += 1

        confusion_type[gt_type][pred_type] += 1
        confusion_priority[gt_priority][pred_priority] += 1

        results.append({
            "case_id": case_id,
            "gt_type": gt_type,
            "pred_type": pred_type,
            "type_match": type_match,
            "gt_priority": gt_priority,
            "pred_priority": pred_priority,
            "priority_match": priority_match,
            "gt_category": gt_category,
            "pred_category": pred_category,
            "category_match": category_match,
            "rules_triggered": [f.rule_id for f in rules]
        })

    type_accuracy = round(type_matches / total * 100, 2)
    priority_accuracy = round(priority_matches / total * 100, 2)
    category_accuracy = round(category_matches / total * 100, 2)

    print("=" * 65)
    print(f"DocuDiff AI — Evaluation Benchmark Results ({total} Curated Clauses)")
    print("=" * 65)
    print(f"Change Type Detection Accuracy : {type_accuracy}% ({type_matches}/{total})")
    print(f"Review Priority Triage Accuracy: {priority_accuracy}% ({priority_matches}/{total})")
    print(f"Semantic Category Alignment    : {category_accuracy}% ({category_matches}/{total})")
    print("-" * 65)
    print("Confusion Matrix (Review Priority):")
    for gt in ["critical", "high", "medium", "low"]:
        row_str = f"  GT {gt:<8}: "
        for pred in ["critical", "high", "medium", "low"]:
            cnt = confusion_priority[gt][pred]
            row_str += f"{pred}={cnt}  "
        print(row_str)
    print("=" * 65)

    metrics_output = {
        "total_cases": total,
        "type_accuracy_pct": type_accuracy,
        "priority_accuracy_pct": priority_accuracy,
        "category_accuracy_pct": category_accuracy,
        "detailed_results": results
    }

    out_file = Path(__file__).resolve().parent / "evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2)
    print(f"Saved evaluation metrics to: {out_file.name}")

if __name__ == "__main__":
    csv_file = Path(__file__).resolve().parent / "labelled_changes.csv"
    evaluate_dataset(csv_file)


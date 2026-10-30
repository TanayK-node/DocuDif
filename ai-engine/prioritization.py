from typing import List, Tuple
from schemas import PriorityLevel, RuleFlag, ChangeType

def compute_priority(
    change_type: ChangeType,
    rule_flags: List[RuleFlag],
    similarity: float = 1.0,
    is_wording_only: bool = False
) -> Tuple[PriorityLevel, List[str]]:
    """
    Deterministically computes review priority based on transparent rule signals
    and structural diff characteristics. Produces explicit human-readable reasons.
    """
    reasons: List[str] = []

    if change_type == "unchanged":
        return "low", ["No textual or semantic difference detected."]

    # Check for Critical triggers first
    has_critical_flag = any(f.severity == "critical" for f in rule_flags)
    if has_critical_flag:
        for f in rule_flags:
            if f.severity == "critical":
                reasons.append(f"Critical trigger: {f.description}")
        return "critical", reasons

    # Add reasons for high severity rule flags
    high_flags = [f for f in rule_flags if f.severity == "high"]
    if high_flags:
        for f in high_flags:
            reasons.append(f"Material rule match: {f.description}")
        return "high", reasons

    # If clause was added or removed entirely
    if change_type == "added":
        reasons.append("New clause or requirement introduced into the document.")
        return "high", reasons

    if change_type == "removed":
        reasons.append("Existing clause or provision removed from the document.")
        return "high", reasons

    # If medium rule flags exist
    medium_flags = [f for f in rule_flags if f.severity == "medium"]
    if medium_flags:
        for f in medium_flags:
            reasons.append(f"Rule alert: {f.description}")
        return "medium", reasons

    # If LLM / similarity indicates wording only
    if is_wording_only or similarity >= 0.95:
        reasons.append("Textual phrasing changed with no material rule or obligation alteration.")
        return "low", reasons

    # Default modified fallback
    reasons.append("Text modified with moderate semantic divergence; requires manual verification.")
    return "medium", reasons


import re
from typing import List, Dict, Any, Tuple, Optional
from schemas import RuleFlag, PriorityLevel

# Regex patterns with proper raw strings avoiding escaping bugs
NUM_UNIT_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:days?|hours?|weeks?|months?|years?|minutes?|seconds?|%|percent|\$|usd|eur|gbp|inr|mb|gb|tb|kb)?\b",
    re.IGNORECASE
)

DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\b",
    re.IGNORECASE
)

MODAL_GROUPS = {
    "mandatory": {"must", "shall", "required", "mandatory", "obligated", "compulsory"},
    "recommendation": {"should", "recommended", "advised", "ought to"},
    "permissive": {"may", "can", "could", "permitted", "allowed", "optional", "authorized"},
    "prohibitive": {"must not", "shall not", "prohibited", "forbidden", "disallowed", "banned", "cannot"}
}

NEGATION_TERMS = {
    "not", "no", "never", "neither", "nor", "none", "without", "except", "cannot",
    "can't", "prohibited", "exclude", "excluding", "non-transferable", "ineligible"
}

SCOPE_TERMS = {
    "only", "solely", "exclusively", "all", "any", "and", "or", "both", "either",
    "auditors", "administrators", "managers", "employees", "supervisors", "directors", "officers"
}

APPROVAL_TERMS = {
    "approval", "approve", "approved", "authorization", "authorize", "authorized",
    "consent", "sign-off", "signed off", "permission", "clearance"
}

CONDITION_TERMS = {
    "if", "unless", "provided that", "subject to", "in the event of", "except when", "conditional upon"
}

def extract_tokens_matching(text: str, vocab: set) -> List[str]:
    words = re.findall(r"\b[a-z'-]+\b", text.lower())
    return [w for w in words if w in vocab]

def analyze_rule_differences(old_text: str, new_text: str) -> List[RuleFlag]:
    """
    Run comprehensive deterministic rule checks comparing old_text and new_text.
    Returns structured list of RuleFlag instances.
    """
    flags: List[RuleFlag] = []
    old_lower = old_text.lower() if old_text else ""
    new_lower = new_text.lower() if new_text else ""

    # 1. Number & Quantity Changes
    old_nums = [n.strip() for n in NUM_UNIT_RE.findall(old_text)] if old_text else []
    new_nums = [n.strip() for n in NUM_UNIT_RE.findall(new_text)] if new_text else []
    if old_nums != new_nums:
        # Determine if quantities actually differ
        if set(old_nums) != set(new_nums):
            flags.append(RuleFlag(
                rule_id="RULE_NUMERIC_CHANGE",
                category="Numeric, date or duration changed",
                description=f"Quantity or duration modified: '{', '.join(old_nums) or 'none'}' → '{', '.join(new_nums) or 'none'}'",
                severity="high",
                old_value=", ".join(old_nums),
                new_value=", ".join(new_nums)
            ))

    # 2. Date Changes
    old_dates = [d.strip() for d in DATE_RE.findall(old_text)] if old_text else []
    new_dates = [d.strip() for d in DATE_RE.findall(new_text)] if new_text else []
    if set(old_dates) != set(new_dates):
        flags.append(RuleFlag(
            rule_id="RULE_DATE_CHANGE",
            category="Numeric, date or duration changed",
            description=f"Date reference changed: '{', '.join(old_dates) or 'none'}' → '{', '.join(new_dates) or 'none'}'",
            severity="high",
            old_value=", ".join(old_dates),
            new_value=", ".join(new_dates)
        ))

    # 3. Modal / Obligation Shift (e.g. should -> must)
    def detect_modal_group(text: str):
        found = set()
        for group_name, terms in MODAL_GROUPS.items():
            for t in terms:
                if re.search(r"\b" + re.escape(t) + r"\b", text):
                    found.add(group_name)
        return found

    old_modals = detect_modal_group(old_lower)
    new_modals = detect_modal_group(new_lower)
    if old_modals != new_modals:
        # Determine severity: shifting from recommendation/permissive to mandatory is high/critical
        severity: PriorityLevel = "high"
        desc = f"Obligation level shifted from {sorted(list(old_modals)) or ['neutral']} to {sorted(list(new_modals)) or ['neutral']}"
        if ("recommendation" in old_modals or "permissive" in old_modals) and "mandatory" in new_modals:
            desc = "Obligation elevated: requirement changed from recommended/permitted to mandatory (e.g., 'should' → 'must')"
            severity = "high"
        elif "mandatory" in old_modals and ("permissive" in new_modals or not new_modals):
            desc = "Obligation relaxed: mandatory requirement removed or made optional"
            severity = "high"

        flags.append(RuleFlag(
            rule_id="RULE_MODAL_OBLIGATION_CHANGE",
            category="Meaning or obligation changed",
            description=desc,
            severity=severity,
            old_value=", ".join(sorted(list(old_modals))),
            new_value=", ".join(sorted(list(new_modals)))
        ))

    # 4. Scope, Role & Permission Changes (e.g. administrators only -> administrators and auditors)
    old_scope = extract_tokens_matching(old_lower, SCOPE_TERMS)
    new_scope = extract_tokens_matching(new_lower, SCOPE_TERMS)
    if set(old_scope) != set(new_scope):
        # Look for expansion or restriction
        added_roles = [r for r in new_scope if r not in old_scope]
        removed_roles = [r for r in old_scope if r not in new_scope]
        desc_parts = []
        if added_roles:
            desc_parts.append(f"expanded permissions/actors: +{', '.join(added_roles)}")
        if removed_roles:
            desc_parts.append(f"removed permissions/actors: -{', '.join(removed_roles)}")
        flags.append(RuleFlag(
            rule_id="RULE_PERMISSION_SCOPE_CHANGE",
            category="Permission, role or access-scope changed",
            description=f"Permission or access scope modified ({'; '.join(desc_parts)})",
            severity="high",
            old_value=", ".join(old_scope),
            new_value=", ".join(new_scope)
        ))

    # 5. Negation or Exclusion Changes
    old_negs = extract_tokens_matching(old_lower, NEGATION_TERMS)
    new_negs = extract_tokens_matching(new_lower, NEGATION_TERMS)
    if set(old_negs) != set(new_negs):
        flags.append(RuleFlag(
            rule_id="RULE_NEGATION_CHANGE",
            category="Negation or exception changed",
            description=f"Negation / exception modifier changed: '{', '.join(old_negs) or 'none'}' → '{', '.join(new_negs) or 'none'}'",
            severity="critical",
            old_value=", ".join(old_negs),
            new_value=", ".join(new_negs)
        ))

    # 6. Condition & Approval Requirements (e.g., manager approval required)
    old_approvals = extract_tokens_matching(old_lower, APPROVAL_TERMS)
    new_approvals = extract_tokens_matching(new_lower, APPROVAL_TERMS)
    if not old_approvals and new_approvals:
        flags.append(RuleFlag(
            rule_id="RULE_APPROVAL_ADDED",
            category="Condition, approval or process changed",
            description=f"New approval requirement introduced: '{', '.join(new_approvals)}'",
            severity="high",
            old_value="",
            new_value=", ".join(new_approvals)
        ))
    elif old_approvals and not new_approvals:
        flags.append(RuleFlag(
            rule_id="RULE_APPROVAL_REMOVED",
            category="Condition, approval or process changed",
            description=f"Approval requirement removed: '{', '.join(old_approvals)}'",
            severity="high",
            old_value=", ".join(old_approvals),
            new_value=""
        ))

    return flags


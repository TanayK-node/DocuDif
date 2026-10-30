from typing import List, Dict, Any, Set, Tuple, Optional
import numpy as np
from normalization import normalize_for_matching

DEFAULT_SEMANTIC_THRESHOLD = 0.65

def align_units(
    old_units: List[Dict[str, Any]],
    new_units: List[Dict[str, Any]],
    old_embeddings: Optional[np.ndarray] = None,
    new_embeddings: Optional[np.ndarray] = None,
    threshold: float = DEFAULT_SEMANTIC_THRESHOLD
) -> Dict[str, Any]:
    """
    Performs a strict two-pass one-to-one alignment:
    1. Exact normalized text matches (similarity = 1.0, method = 'exact').
    2. High-similarity semantic matches (similarity >= threshold, method = 'semantic').
    
    Returns:
      - 'matches': list of matched pairs (old_unit, new_unit, similarity, match_method)
      - 'unmatched_old': list of remaining old units (removals)
      - 'unmatched_new': list of remaining new units (additions)
    """
    used_old: Set[int] = set()
    used_new: Set[int] = set()
    matches: List[Dict[str, Any]] = []

    # Map normalized text to list of old indices
    old_norm_map: Dict[str, List[int]] = {}
    for i, u in enumerate(old_units):
        key = normalize_for_matching(u["text"])
        if key:
            old_norm_map.setdefault(key, []).append(i)

    # Pass 1: Exact normalized matches (preferring closest relative position)
    for j, nu in enumerate(new_units):
        key = normalize_for_matching(nu["text"])
        if not key:
            continue
        candidates = [i for i in old_norm_map.get(key, []) if i not in used_old]
        if candidates:
            # Pick candidate with closest relative index
            best_i = min(candidates, key=lambda c: abs(c / max(1, len(old_units)) - j / max(1, len(new_units))))
            used_old.add(best_i)
            used_new.add(j)
            matches.append({
                "old_idx": best_i,
                "new_idx": j,
                "old_unit": old_units[best_i],
                "new_unit": nu,
                "similarity": 1.0,
                "match_method": "exact"
            })

    # Pass 2: Semantic vector alignment for remaining items
    remaining_old_indices = [i for i in range(len(old_units)) if i not in used_old]
    remaining_new_indices = [j for j in range(len(new_units)) if j not in used_new]

    if (
        remaining_old_indices
        and remaining_new_indices
        and old_embeddings is not None
        and new_embeddings is not None
        and len(old_embeddings) > 0
        and len(new_embeddings) > 0
    ):
        sub_old_vecs = old_embeddings[remaining_old_indices]
        sub_new_vecs = new_embeddings[remaining_new_indices]

        # Cosine similarity matrix (since vectors are L2-normalized)
        sim_matrix = np.dot(sub_old_vecs, sub_new_vecs.T)

        candidate_pairs = []
        for r_old, orig_old in enumerate(remaining_old_indices):
            for r_new, orig_new in enumerate(remaining_new_indices):
                sim = float(sim_matrix[r_old, r_new])
                if sim >= threshold:
                    candidate_pairs.append((sim, orig_old, orig_new))

        # Sort candidate pairs descending by similarity
        candidate_pairs.sort(key=lambda x: x[0], reverse=True)

        for sim, orig_old, orig_new in candidate_pairs:
            if orig_old not in used_old and orig_new not in used_new:
                used_old.add(orig_old)
                used_new.add(orig_new)
                matches.append({
                    "old_idx": orig_old,
                    "new_idx": orig_new,
                    "old_unit": old_units[orig_old],
                    "new_unit": new_units[orig_new],
                    "similarity": round(sim, 4),
                    "match_method": "semantic"
                })

    unmatched_old = [old_units[i] for i in range(len(old_units)) if i not in used_old]
    unmatched_new = [new_units[j] for j in range(len(new_units)) if j not in used_new]

    return {
        "matches": matches,
        "unmatched_old": unmatched_old,
        "unmatched_new": unmatched_new
    }


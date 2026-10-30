import re
from typing import List, Dict, Any

COMMON_ABBREVS = {"e.g.", "i.e.", "etc.", "mr.", "mrs.", "ms.", "dr.", "vs.", "inc.", "ltd.", "corp.", "co.", "dept.", "no."}

def split_into_clauses_or_sentences(text: str) -> List[str]:
    """
    Split a paragraph into sentence or clause units, handling abbreviations,
    numbered clauses, bullet points, and semicolons.
    """
    text = text.strip()
    if not text:
        return []

    # Check for bullet points or multiple lines within paragraph
    if "\n" in text:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        result = []
        for line in lines:
            result.extend(split_into_clauses_or_sentences(line))
        return result

    # Sentence splitting by punctuation followed by capital letter or quote
    raw_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(])", text)
    if not raw_splits:
        return [text]

    # Re-combine if split occurred after a known abbreviation
    sentences: List[str] = []
    for part in raw_splits:
        part = part.strip()
        if not part:
            continue
        if sentences:
            last_token = sentences[-1].split()[-1].lower() if sentences[-1].split() else ""
            if last_token in COMMON_ABBREVS:
                # Merge back
                sentences[-1] = sentences[-1] + " " + part
                continue
        sentences.append(part)

    return sentences

def is_likely_heading(text: str) -> bool:
    """Heuristic for detecting titles/headings."""
    cleaned = text.strip()
    if len(cleaned) < 80 and not cleaned.endswith((".", ";", ":", ",")) and "\n" not in cleaned:
        return True
    return False

def segment_document(records: List[Dict[str, Any]], doc_prefix: str = "doc") -> List[Dict[str, Any]]:
    """
    Transform raw extracted paragraph/table records into granular,
    sentence/clause-level comparison units while maintaining full provenance.
    """
    units = []
    unit_counter = 1

    for rec in records:
        raw_text = rec["text"].strip()
        if not raw_text:
            continue

        # If it's a table row, keep it as a comparison unit
        if rec.get("table") is not None:
            units.append({
                "unit_id": f"{doc_prefix}_u{unit_counter:04d}",
                "text": raw_text,
                "page": rec.get("page"),
                "paragraph": rec.get("paragraph"),
                "sentence_idx": 1,
                "table": rec.get("table"),
                "row": rec.get("row"),
                "source": rec.get("source"),
                "is_heading": False
            })
            unit_counter += 1
            continue

        # Split paragraph into sentence/clause units
        sentences = split_into_clauses_or_sentences(raw_text)
        para_idx = rec.get("paragraph")
        page_idx = rec.get("page")
        source_name = rec.get("source")

        for s_idx, sentence_text in enumerate(sentences, start=1):
            units.append({
                "unit_id": f"{doc_prefix}_u{unit_counter:04d}",
                "text": sentence_text,
                "page": page_idx,
                "paragraph": para_idx,
                "sentence_idx": s_idx,
                "table": None,
                "row": None,
                "source": source_name,
                "is_heading": is_likely_heading(sentence_text) and len(sentences) == 1
            })
            unit_counter += 1

    return units

import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Standardize whitespace and unicode characters while preserving numbers,
    punctuation, and case essential for diffing.
    """
    if not text:
        return ""
    # Normalize unicode (e.g. smart quotes, non-breaking spaces)
    text = unicodedata.normalize("NFKC", text)
    # Replace unusual quotes/dashes with standard ascii
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
    text = text.replace("—", " - ").replace("–", " - ")
    # Replace non-breaking spaces
    text = text.replace("\u00a0", " ")
    # Standardize whitespace: multiple spaces/tabs into single space, keep single newlines if present
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines).strip()

def normalize_for_matching(text: str) -> str:
    """
    Normalizes text strictly for exact-matching hashes:
    lowercase, strips non-alphanumeric (except basic math/currency symbols),
    and collapses all spaces.
    """
    if not text:
        return ""
    t = text.lower()
    t = unicodedata.normalize("NFKC", t)
    # Strip punctuation except essential semantic characters
    t = re.sub(r"[^\w%$@/.-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


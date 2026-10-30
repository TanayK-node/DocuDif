import re
from typing import List, Tuple
import difflib
from schemas import TokenDiff

def tokenize_words_and_spaces(text: str) -> List[str]:
    """Split text into words, punctuation, and whitespace tokens preserving exact characters."""
    if not text:
        return []
    # Tokenize by word characters, non-word characters, and whitespace
    return re.findall(r"\w+|[^\w\s]|\s+", text)

def compute_token_diff(old_text: str, new_text: str) -> List[TokenDiff]:
    """
    Compute word-level diff operations (equal, insert, delete) between two texts.
    Returns structured TokenDiff list suitable for UI rendering.
    """
    if not old_text and not new_text:
        return []
    if not old_text:
        return [TokenDiff(operation="insert", text=new_text)]
    if not new_text:
        return [TokenDiff(operation="delete", text=old_text)]

    old_tokens = tokenize_words_and_spaces(old_text)
    new_tokens = tokenize_words_and_spaces(new_text)

    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
    diffs: List[TokenDiff] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            diffs.append(TokenDiff(operation="equal", text="".join(old_tokens[i1:i2])))
        elif tag == "delete":
            diffs.append(TokenDiff(operation="delete", text="".join(old_tokens[i1:i2])))
        elif tag == "insert":
            diffs.append(TokenDiff(operation="insert", text="".join(new_tokens[j1:j2])))
        elif tag == "replace":
            diffs.append(TokenDiff(operation="delete", text="".join(old_tokens[i1:i2])))
            diffs.append(TokenDiff(operation="insert", text="".join(new_tokens[j1:j2])))

    return diffs


import os
import re
from pathlib import Path
from typing import List, Dict, Any, Union
import pymupdf  # PyMuPDF
from docx import Document

class DocumentExtractionError(Exception):
    pass

def extract_document(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Extract structured text units from PDF, DOCX, or TXT documents.
    Preserves document structure (page, paragraph, table, row, source file).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    records: List[Dict[str, Any]] = []

    if ext == ".pdf":
        try:
            doc = pymupdf.open(path)
            para_counter = 1
            for page_idx, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                # Split paragraphs by double newline or block patterns
                raw_paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
                for p_text in raw_paras:
                    records.append({
                        "text": p_text,
                        "page": page_idx,
                        "paragraph": para_counter,
                        "source": path.name,
                        "table": None,
                        "row": None
                    })
                    para_counter += 1
            if not records:
                raise DocumentExtractionError(
                    f"No extractable text found in '{path.name}'. The PDF may be scanned or empty. OCR is not supported in this MVP."
                )
        except Exception as e:
            if isinstance(e, DocumentExtractionError):
                raise
            raise DocumentExtractionError(f"Failed to read PDF '{path.name}': {str(e)}")

    elif ext == ".docx":
        try:
            doc = Document(path)
            para_counter = 1
            for idx, p in enumerate(doc.paragraphs, start=1):
                txt = p.text.strip()
                if txt:
                    records.append({
                        "text": txt,
                        "page": None,
                        "paragraph": para_counter,
                        "source": path.name,
                        "table": None,
                        "row": None
                    })
                    para_counter += 1

            # Preserve tables
            for t_idx, table in enumerate(doc.tables, start=1):
                for r_idx, row in enumerate(table.rows, start=1):
                    row_txt = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_txt:
                        records.append({
                            "text": row_txt,
                            "page": None,
                            "paragraph": None,
                            "source": path.name,
                            "table": t_idx,
                            "row": r_idx
                        })
            if not records:
                raise DocumentExtractionError(f"No readable text or tables found in Word document '{path.name}'.")
        except Exception as e:
            if isinstance(e, DocumentExtractionError):
                raise
            raise DocumentExtractionError(f"Failed to read DOCX '{path.name}': {str(e)}")

    elif ext in [".txt", ".md", ".csv"]:
        try:
            content = path.read_text(encoding="utf-8-sig", errors="replace")
            # If double newline exists, treat as paragraphs.
            # If lines are separated by single newlines, check if each line is non-trivial.
            if "\n\n" in content:
                raw_paras = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
            else:
                raw_paras = [p.strip() for p in content.splitlines() if p.strip()]

            for idx, para in enumerate(raw_paras, start=1):
                records.append({
                    "text": para,
                    "page": None,
                    "paragraph": idx,
                    "source": path.name,
                    "table": None,
                    "row": None
                })
            if not records:
                raise DocumentExtractionError(f"File '{path.name}' is empty.")
        except Exception as e:
            if isinstance(e, DocumentExtractionError):
                raise
            raise DocumentExtractionError(f"Failed to read text file '{path.name}': {str(e)}")
    else:
        raise DocumentExtractionError(f"Unsupported file format '{ext}'. Supported formats: .pdf, .docx, .txt")

    return records


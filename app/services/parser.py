"""
app/services/parser.py
Extracts full text from a PDF using pypdf.
"""

import json
import os
import re
from pathlib import Path


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _clean_extracted_text(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = _normalize_text(raw_line)
        if not line or len(line) < 4:
            continue
        if re.fullmatch(r"page\s*\d+", line, re.IGNORECASE):
            continue
        if re.fullmatch(r"[-=_]{3,}", line):
            continue
        cleaned_lines.append(line)
    cleaned_text = "\n".join(cleaned_lines)
    return re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()


def parse_pdf(pdf_path: str) -> dict:
    from pypdf import PdfReader

    filename = Path(pdf_path).name
    print(f"📄 Parsing PDF: {filename}")

    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    cleaned_text = _clean_extracted_text(full_text)

    if not cleaned_text.strip():
        raise ValueError(
            "No usable text extracted from PDF. "
            "Make sure it's a text-based PDF."
        )

    print(f"✅ PDF parsed: {len(cleaned_text)} characters extracted")
    return {"document_name": filename, "text": cleaned_text}


def save_contract_json(data: dict, output_path: str = "data/processed/contract.json") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Contract saved: {output_path}")
    return output_path


def load_contract_json(path: str = "data/processed/contract.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Contract JSON not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
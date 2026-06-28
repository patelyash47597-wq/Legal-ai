"""
app/services/parser.py
Extracts full text from a PDF using unstructured and removes OCR/form noise.
"""

import json
import os
import re
import shutil
import traceback
from pathlib import Path

import pytesseract

# ----------------------------------------
# TESSERACT PATH (supports Linux/Render)
# ----------------------------------------

configured_tesseract = os.getenv("TESSERACT_CMD")
if configured_tesseract and os.path.exists(configured_tesseract):
    pytesseract.pytesseract.tesseract_cmd = configured_tesseract
else:
    detected = shutil.which("tesseract")
    if detected:
        pytesseract.pytesseract.tesseract_cmd = detected

FORM_FIELD_PATTERNS = [
    r"^EMPLOYEE\s+NAME$",
    r"^ADDRESS$",
    r"^PHONE$",
    r"^DATE$",
    r"^SOCIAL\s+SECURITY\s+NUMBER$",
    r"^SSN$",
    r"^SIGNATURE$",
    r"^EMAIL$",
    r"^E-MAIL$",
]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _is_noise_or_form_label(text: str) -> bool:
    line = _normalize_text(text)
    if not line:
        return True
    if len(line) < 4:
        return True
    if re.fullmatch(r"page\s*\d+", line, re.IGNORECASE):
        return True
    if re.fullmatch(r"[-=_]{3,}", line):
        return True
    if any(re.fullmatch(pattern, line, re.IGNORECASE) for pattern in FORM_FIELD_PATTERNS):
        return True
    lowered = line.lower()
    if len(line.split()) <= 3 and any(
        token in lowered for token in [
            "employee name", "address", "phone", "date",
            "social security number", "ssn", "signature", "email",
        ]
    ):
        return True
    return False


def _clean_extracted_text(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = _normalize_text(raw_line)
        if not line:
            continue
        if _is_noise_or_form_label(line):
            continue
        cleaned_lines.append(line)
    cleaned_text = "\n".join(cleaned_lines)
    return re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()


# ----------------------------------------
# PARSE PDF → TEXT
# ----------------------------------------

def parse_pdf(pdf_path: str) -> dict:
    from unstructured.partition.pdf import partition_pdf

    filename = Path(pdf_path).name
    print(f"📄 Parsing PDF: {filename}")

    elements = None
    last_error = None

    try:
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
        )
    except Exception as exc:
        last_error = exc
        print(f"⚠️ hi_res parsing failed for {filename}: {exc}")

    if elements is None:
        try:
            elements = partition_pdf(
                filename=pdf_path,
                strategy="fast",
                infer_table_structure=False,
            )
            print(f"✅ Fallback parsing succeeded for {filename} using fast strategy")
        except Exception as exc:
            last_error = exc
            print(f"⚠️ fast parsing failed for {filename}: {exc}")

    if elements is None:
        raise ValueError(f"Unable to parse PDF with available strategies. Last error: {last_error}")

    full_text = ""
    for el in elements:
        text = getattr(el, "text", None)
        if text:
            full_text += text + "\n"

    cleaned_text = _clean_extracted_text(full_text)

    if not cleaned_text.strip():
        raise ValueError(
            "No usable text extracted from PDF. "
            "Make sure it's a text-based PDF or the OCR output is readable."
        )

    output = {
        "document_name": filename,
        "text": cleaned_text,
    }

    print(f"✅ PDF parsed: {len(cleaned_text)} characters extracted")
    return output


# ----------------------------------------
# SAVE CONTRACT JSON
# ----------------------------------------

def save_contract_json(data: dict, output_path: str = "data/processed/contract.json") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Contract saved: {output_path}")
    return output_path


# ----------------------------------------
# LOAD EXISTING CONTRACT JSON
# ----------------------------------------

def load_contract_json(path: str = "data/processed/contract.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Contract JSON not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
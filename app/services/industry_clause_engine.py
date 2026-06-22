"""
app/services/industry_clause_engine.py
Segments contract text into semantic clauses while filtering OCR/form noise.
"""

import json
import os
import re

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer

print("🔄 Loading NLP models...")

_nlp = None
_model = None

CLAUSE_TYPE_KEYWORDS = {
    "Definition": ["definition", "defined", "means"],
    "Exclusions": ["exclusion", "excluded", "except", "excepted"],
    "Confidentiality": ["confidential", "non-disclosure", "non disclosure", "proprietary", "trade secret", "secret information"],
    "Payment": ["pay", "payment", "invoice", "fees", "compensation", "salary", "remit", "due date", "amount due"],
    "Obligations": ["obligation", "obligations", "duty", "duties", "undertake", "comply"],
    "Return of Information": ["return of information", "return information", "return", "destroy", "delete", "cease use"],
    "Term": ["term", "duration", "period", "effective date", "commence", "expire", "expiration"],
    "Amendment": ["amend", "amendment", "modify", "revise", "change"],
    "Relationship": ["independent contractor", "employer", "employee", "agency", "relationship", "parties"],
    "Severability": ["severability", "severable", "invalid provision", "unenforceable"],
    "Integration": ["entire agreement", "integration", "incorporated", "supersedes", "merger", "complete agreement"],
    "Waiver": ["waiver", "waive", "relinquish"],
    "Notice": ["notice", "notify", "written notice"],
    "Binding Effect": ["binding effect", "bind", "binding"],
    "Signature": ["signature", "signed by", "signed"],
    "Liability": ["liability", "liable", "damages", "loss", "harm", "responsibility"],
    "Indemnification": ["indemnify", "indemnity", "defend", "hold harmless", "reimburse"],
    "Governing Law": ["governing law", "applicable law", "jurisdiction", "state law", "federal law"],
    "Dispute Resolution": ["dispute", "arbitration", "mediation", "litigation", "venue"],
    "Intellectual Property": ["intellectual property", "copyright", "patent", "trademark", "trade secret", "ip"],
    "General": [],
}


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _get_model():
    global _model
    if _model is None:
        print("🔄 Loading InLegalBERT...")
        _model = SentenceTransformer("law-ai/InLegalBERT")
        print("✅ InLegalBERT loaded")
    return _model


def _normalize_text(text: str) -> str:
    """Normalizes whitespace while preserving paragraph boundaries for section extraction."""

    return re.sub(r"\s+", " ", text or "").strip()


def is_heading(text: str) -> bool:
    """Detects numbered and titled contract sections while preserving their body text as part of the clause."""

    candidate = _normalize_text(text).strip(" .:-")
    if not candidate:
        return False

    if len(candidate.split()) > 12:
        return False

    normalized = candidate.lower()
    if re.match(r"^(?:section|article|part|clause)\s*\d+", normalized):
        return True

    if re.match(r"^(?:\d+|[ivxlcdm]+)[\s\.:\-)]*$", candidate, re.IGNORECASE):
        return True

    if re.match(r"^(?:\d+|[ivxlcdm]+)[\s\.:\-)]*(definition|exclusions|term|amendment|notice|waiver|integration|severability|governing law|dispute resolution|payment|liability|indemnification|intellectual property|binding effect|signature|confidentiality|obligations|return of information)\b", normalized):
        return True

    heading_keywords = [
        "definition",
        "exclusions",
        "confidentiality",
        "obligations",
        "return of information",
        "term",
        "amendment",
        "relationship",
        "severability",
        "integration",
        "waiver",
        "notice",
        "binding effect",
        "signature",
        "payment",
        "liability",
        "indemnification",
        "governing law",
        "dispute resolution",
        "intellectual property",
        "section",
        "article",
        "part",
        "clause",
    ]
    return any(keyword in normalized for keyword in heading_keywords) and len(candidate.split()) <= 12


def is_signature_block(text: str) -> bool:
    """Detects signature blocks and form-like metadata."""

    candidate = _normalize_text(text).lower()
    if not candidate:
        return False

    signature_keywords = [
        "typed or printed name",
        "employee name",
        "address",
        "phone",
        "signature",
        "signed by",
        "signed",
        "social security number",
        "ssn",
        "email",
        "date",
    ]
    return any(keyword in candidate for keyword in signature_keywords)


def is_metadata(text: str) -> bool:
    """Detects page numbers, copyright text, and other non-clause metadata."""

    candidate = _normalize_text(text).lower()
    if not candidate:
        return False

    metadata_keywords = [
        "copyright",
        "page",
        "typed or printed name",
        "employee name",
        "address",
        "phone",
        "signature",
        "social security number",
        "ssn",
        "email",
        "date",
    ]
    return any(keyword in candidate for keyword in metadata_keywords)


def clean_clause(text: str):
    """Removes metadata, signatures, and other non-clause content while preserving section headings and their body text."""

    if text is None:
        return None

    cleaned = _normalize_text(text)
    if not cleaned:
        return None

    # Remove leading numbering and bullets from lines such as "1. Definition..."
    cleaned = re.sub(r"^[\-\*\d\s\.:)]+", "", cleaned)
    cleaned = cleaned.strip(" .:-")
    if not cleaned:
        return None

    # Skip obvious form metadata and signature blocks.
    if is_signature_block(cleaned) or is_metadata(cleaned):
        return None

    # Keep section titles with their body text so numbering sections become full clauses.
    if is_heading(cleaned):
        cleaned = cleaned

    if len(cleaned.split()) < 8:
        return None

    lower_text = cleaned.lower()
    if any(token in lower_text for token in ["typed or printed name", "copyright", "page", "signature", "employee name", "address", "phone", "date"]):
        return None

    return cleaned


def classify_clause(text: str) -> str:
    """Classifies a clause using specific keywords only; broad words such as 'shall' and 'must' are intentionally omitted."""

    cleaned = clean_clause(text)
    if not cleaned:
        return "Unknown"

    normalized = cleaned.lower()
    for clause_type, keywords in CLAUSE_TYPE_KEYWORDS.items():
        if not keywords:
            continue
        if any(keyword in normalized for keyword in keywords):
            return clause_type
    return "General"


def classify_clause_type(text: str) -> str:
    return classify_clause(text)


def _is_noise_or_form_field(text: str) -> bool:
    line = _normalize_text(text)
    if not line:
        return True

    if len(line) < 8:
        return True

    if re.fullmatch(r"page\s*\d+", line, re.IGNORECASE):
        return True

    if re.fullmatch(r"[-=_]{3,}", line):
        return True

    lowered = line.lower()
    field_keywords = [
        "employee name",
        "address",
        "phone",
        "date",
        "social security number",
        "ssn",
        "signature",
        "email",
        "typed or printed name",
        "copyright",
    ]
    if len(line.split()) <= 3 and any(keyword in lowered for keyword in field_keywords):
        return True

    return False


def _clean_clause_candidate(text: str) -> str:
    cleaned = clean_clause(text)
    if not cleaned or _is_noise_or_form_field(cleaned):
        return ""
    return cleaned


# ----------------------------------------
# EXTRACT CLAUSES FROM TEXT
# ----------------------------------------

def extract_clauses(text: str) -> list:
    """
    Extracts clauses from contract text using numbered section structure rather than semantic merging.

    The method first normalizes and cleans the text, then splits it into sections based on numbered
    headings such as "1. Definition of Confidential Information." The heading and the following content
    are preserved as a single clause. Sentence embeddings are generated for each clause and returned
    for downstream risk analysis.
    """

    nlp = _get_nlp()
    model = _get_model()

    cleaned_text = _normalize_text(text)
    if not cleaned_text:
        raise ValueError("No usable contract text available for clause extraction.")

    # Split the contract using numbered headings (e.g. "1. Definition of Confidential Information.")
    pattern = r"(?=\b\d+\.\s+[A-Z])"
    sections = [section.strip() for section in re.split(pattern, cleaned_text) if section.strip()]

    # If regex splitting does not yield useful sections, fall back to sentence-based extraction.
    if len(sections) < 2:
        doc = nlp(cleaned_text)
        sections = []
        for sent in doc.sents:
            candidate = _clean_clause_candidate(sent.text)
            if candidate:
                sections.append(candidate)

    clauses = []
    for section in sections:
        candidate = clean_clause(section)
        if not candidate:
            continue

        if len(candidate.split()) < 8:
            continue

        if is_heading(candidate):
            clauses.append(candidate)
            continue

        # For flows where section headings and paragraph text are joined as a single text block,
        # preserve the entire block as one clause.
        clauses.append(candidate)

    # Remove metadata-only sections and duplicate content.
    clauses = [clause for clause in clauses if clause and clean_clause(clause) is not None]
    clauses = list(dict.fromkeys(clauses))

    if not clauses:
        raise ValueError("No meaningful clauses were produced after cleaning the extracted text.")

    print(f"✅ Section-based clauses created: {len(clauses)}")

    # Generate embeddings for downstream risk analysis; no semantic merging is performed here.
    sentence_embeddings = model.encode(clauses)

    structured_output = [
        {
            "clause_id": i + 1,
            "text": clause,
            "embedding": sentence_embeddings[i].tolist(),
            "length": len(clause),
            "word_count": len(clause.split()),
            "clause_type": classify_clause_type(clause),
        }
        for i, clause in enumerate(clauses)
    ]

    return structured_output


# ----------------------------------------
# SAVE CLAUSES TO JSON
# ----------------------------------------

def save_clauses(clauses: list, output_path: str = "data/processed/industry_clauses.json") -> str:
    """Saves clause list to JSON file."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clauses, f, indent=4)

    print(f"✅ Clauses saved: {output_path}")
    return output_path


# ----------------------------------------
# LOAD EXISTING CLAUSES
# ----------------------------------------

def load_clauses(path: str = "data/processed/industry_clauses.json") -> list:
    """Loads existing clauses JSON from disk."""

    if not os.path.exists(path):
        raise FileNotFoundError(f"Clauses JSON not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
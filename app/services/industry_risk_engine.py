"""
app/services/risk_engine.py
Converted from: industry_risk_engine.py (script) → reusable functions

Runs full risk analysis pipeline:
- FAISS vector search vs standard clauses
- Isolation Forest anomaly detection
- Percentile-based dynamic thresholds
- Combined risk scoring (similarity 60% + anomaly 40%)
"""

import json
import os
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer
from sklearn.ensemble import IsolationForest
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------------------
# SINGLETON: LOAD ONCE
# ----------------------------------------

_model      = None
_index      = None
_iso_forest = None
_std_data   = None
_std_embs   = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("🔄 Loading InLegalBERT for risk engine...")
        _model = SentenceTransformer("law-ai/InLegalBERT")
        print("✅ Model loaded")
    return _model


def _load_standard_data(
    standard_path: str = "data/processed/standard_clauses.json"
):
    """Loads standard clauses and builds FAISS index + IsoForest."""

    global _index, _iso_forest, _std_data, _std_embs

    if _index is not None:
        return  # already loaded

    model = _get_model()

    # Load standard clauses JSON
    with open(standard_path, "r", encoding="utf-8") as f:
        _std_data = json.load(f)

    # Generate standard embeddings (chunked)
    _std_embs = np.array([
        _encode_clause(item["text"], model)
        for item in _std_data
    ]).astype("float32")

    # Build FAISS index
    dim    = _std_embs.shape[1]
    _index = faiss.IndexFlatL2(dim)
    _index.add(_std_embs)
    print(f"✅ FAISS index built: {_index.ntotal} standard clauses")

    # Train Isolation Forest
    _iso_forest = IsolationForest(
        contamination="auto",
        n_estimators=200,
        random_state=42
    )
    _iso_forest.fit(_std_embs)
    print("✅ Isolation Forest trained")


# ----------------------------------------
# CHUNKED ENCODING
# Handles clauses > 512 tokens (BERT limit)
# ----------------------------------------

def _encode_clause(
    text: str,
    model: SentenceTransformer,
    max_words: int = 400,
    overlap: int = 50
) -> np.ndarray:
    """
    Encodes a long clause by splitting into
    overlapping chunks and mean-pooling embeddings.
    """

    words = text.split()

    if len(words) <= max_words:
        return model.encode([text])[0]

    chunks = []
    for i in range(0, len(words), max_words - overlap):
        chunk = " ".join(words[i: i + max_words])
        chunks.append(chunk)

    embeddings = model.encode(chunks)
    return np.mean(embeddings, axis=0)


# ----------------------------------------
# MAIN RISK ANALYSIS FUNCTION
# ----------------------------------------

def analyze_risk(
    contract_data: list,
    standard_path: str = "data/processed/standard_clauses.json"
) -> list:
    """
    Runs full risk analysis on extracted clauses.

    Args:
        contract_data: List of clause dicts
                       (from clause_engine.extract_clauses)
        standard_path: Path to standard_clauses.json

    Returns:
        List of result dicts with risk scores and levels
    """

    model = _get_model()
    _load_standard_data(standard_path)

    # ----------------------------------------
    # STEP 1: CALIBRATE THRESHOLDS
    # Compute similarity for all clauses first,
    # then set percentile-based thresholds
    # ----------------------------------------

    print("⏳ Calibrating thresholds...")

    all_similarities = []

    for clause in contract_data:

        emb = np.array(
            _encode_clause(clause["text"], model)
        ).astype("float32").reshape(1, -1)

        _, indices = _index.search(emb, k=1)
        matched_idx = indices[0][0]

        sim = cosine_similarity(
            emb,
            [_std_embs[matched_idx]]
        )[0][0]

        all_similarities.append(float(sim))

    # Percentile-based thresholds (data-driven)
    HIGH_THRESH = float(np.percentile(all_similarities, 25))
    MED_THRESH  = float(np.percentile(all_similarities, 50))

    print(
        f"✅ Thresholds — "
        f"HIGH < {HIGH_THRESH:.3f} | "
        f"MEDIUM < {MED_THRESH:.3f}"
    )

    # ----------------------------------------
    # STEP 2: SCORE EACH CLAUSE
    # ----------------------------------------

    results = []

    for clause in contract_data:

        clause_text = clause["text"]

        # Encode
        clause_emb = np.array(
            _encode_clause(clause_text, model)
        ).astype("float32").reshape(1, -1)

        # FAISS search
        _, indices = _index.search(clause_emb, k=1)
        matched_idx    = indices[0][0]
        matched_clause = _std_data[matched_idx]

        # Cosine similarity
        similarity = cosine_similarity(
            clause_emb,
            [_std_embs[matched_idx]]
        )[0][0]

        # Anomaly score (sigmoid mapped, 0=normal, 1=anomalous)
        raw_score    = _iso_forest.score_samples(clause_emb)[0]
        anomaly_score = 1 / (1 + np.exp(5 * raw_score))

        # Combined risk (60% similarity + 40% anomaly)
        combined_risk = (1 - similarity) * 0.6 + anomaly_score * 0.4

        # Risk level
        if similarity < HIGH_THRESH or combined_risk > 0.55:
            risk = "HIGH"
        elif similarity < MED_THRESH or combined_risk > 0.30:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        results.append({
            "contract_clause":         clause_text,
            "matched_standard_clause": matched_clause["text"],
            "clause_type":             matched_clause["type"],
            "similarity_score":        float(similarity),
            "anomaly_score":           float(anomaly_score),
            "combined_risk_score":     float(combined_risk),
            "risk_level":              risk
        })

    # ----------------------------------------
    # SUMMARY LOG
    # ----------------------------------------

    total  = len(results)
    high   = sum(1 for r in results if r["risk_level"] == "HIGH")
    medium = sum(1 for r in results if r["risk_level"] == "MEDIUM")
    low    = sum(1 for r in results if r["risk_level"] == "LOW")

    print(f"\n📊 Risk Summary:")
    print(f"   Total   : {total}")
    print(f"   HIGH    : {high}  ({100*high//total if total else 0}%)")
    print(f"   MEDIUM  : {medium} ({100*medium//total if total else 0}%)")
    print(f"   LOW     : {low}  ({100*low//total if total else 0}%)")

    return results


# ----------------------------------------
# SAVE / LOAD RISK RESULTS
# ----------------------------------------

def save_risk_results(
    results: list,
    output_path: str = "data/processed/industry_risk_analysis.json"
) -> str:
    """Saves risk analysis results to JSON."""

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"✅ Risk results saved: {output_path}")
    return output_path


def load_risk_results(
    path: str = "data/processed/industry_risk_analysis.json"
) -> list:
    """Loads existing risk results JSON from disk."""

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Risk results not found at: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
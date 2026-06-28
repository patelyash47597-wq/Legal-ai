"""
app/services/risk_engine.py
Risk analysis using category-aware FAISS search and anomaly detection.
"""

import json
import os

from app.services.industry_clause_engine import classify_clause, clean_clause, classify_clause_type

MIN_SIMILARITY = 0.50

HIGH_RISK_PATTERNS = [
    "without prior consent",
    "any third party",
    "no liability",
    "waives all claims",
    "without notice",
    "without notifying",
    "sole discretion",
    "unilateral",
    "shall not have such rights",
    "not responsible",
    "may disclose confidential information",
    "may share confidential information",
    "bear no liability",
    "terminate immediately",
    "modify this agreement at any time",
]

MEDIUM_RISK_PATTERNS = [
    "reasonable efforts",
    "best efforts",
    "may terminate",
    "limited liability",
]

LOW_RISK_PATTERNS = [
    "governing law",
    "severability",
    "waiver",
    "binding effect",
    "return or destroy",
    "entire agreement",
]

_model = None
_standard_indexes = None
_iso_forest = None
_std_data = None
_std_embeddings = None


def _get_model():
    from sentence_transformers import SentenceTransformer
    global _model
    if _model is None:
        try:
            print("🔄 Loading InLegalBERT for risk engine...")
            _model = SentenceTransformer("law-ai/InLegalBERT")
            print("✅ Risk engine model loaded")
        except Exception as exc:
            print(f"⚠️ Could not load risk model: {exc}")
            print("   This may be due to missing HF_TOKEN environment variable")
            print("   Set HF_TOKEN on Render Dashboard → Settings → Environment")
            print("   Get it from: https://huggingface.co/settings/tokens")
            _model = None
    return _model


def _encode_clause(text, model, max_words=400, overlap=50):
    import numpy as np
    words = text.split()
    if len(words) <= max_words:
        return model.encode([text])[0]
    chunks = []
    for i in range(0, len(words), max_words - overlap):
        chunk = " ".join(words[i : i + max_words])
        chunks.append(chunk)
    embeddings = model.encode(chunks)
    return np.mean(embeddings, axis=0)


def _normalize_standard_items(payload):
    if isinstance(payload, dict):
        if "clauses" in payload:
            items = payload["clauses"]
        elif "data" in payload:
            items = payload["data"]
        else:
            items = list(payload.values())
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("Unsupported standard clause dataset format")

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content") or item.get("clause") or item.get("body")
        if not text:
            continue
        clause_type = item.get("type") or item.get("clause_type") or classify_clause_type(text)
        normalized.append({
            "text": text,
            "clause_type": clause_type,
            "metadata": item.get("metadata", {}),
        })

    return normalized


def _load_standard_data(standard_path):
    import faiss
    import numpy as np
    from sklearn.ensemble import IsolationForest
    global _standard_indexes, _iso_forest, _std_data, _std_embeddings

    if _standard_indexes is not None:
        return

    if not os.path.exists(standard_path):
        raise FileNotFoundError(
            f"standard_clauses.json not found at: {standard_path}\n"
            "Please make sure this file exists in data/processed/"
        )

    model = _get_model()

    with open(standard_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    _std_data = _normalize_standard_items(payload)
    if not _std_data:
        raise ValueError("Standard clause dataset is empty.")

    print(f"✅ Standard clauses loaded: {len(_std_data)}")

    grouped_items = {}
    for item in _std_data:
        grouped_items.setdefault(item["clause_type"], []).append(item)

    if model is not None:
        _std_embeddings = []
        grouped_indexes = {}
        for clause_type, items in grouped_items.items():
            embeddings = np.array([_encode_clause(item["text"], model) for item in items]).astype("float32")
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(embeddings)
            grouped_indexes[clause_type] = {
                "index": index,
                "items": items,
                "embeddings": embeddings,
            }
            _std_embeddings.append(embeddings)

        _standard_indexes = grouped_indexes
        all_embeddings = np.vstack(_std_embeddings).astype("float32")

        if len(_std_data) < 50:
            _iso_forest = None
            print("⚠️ Isolation Forest disabled because the standard dataset has fewer than 50 clauses")
        else:
            _iso_forest = IsolationForest(contamination="auto", n_estimators=200, random_state=42)
            _iso_forest.fit(all_embeddings)
            print("✅ Isolation Forest trained")

        print(f"✅ FAISS indexes built for {len(_standard_indexes)} clause categories")
    else:
        _standard_indexes = {}
        _iso_forest = None
        print("⚠️ FAISS and anomaly scoring are disabled because embeddings could not be loaded.")


def evaluate_clause_risk(
    clause_text: str,
    similarity_score: float = 0.0,
    anomaly_score: float = 0.0,
    matched_clause: dict | None = None,
) -> dict:
    normalized_clause = (clause_text or "").lower()
    matched_patterns = []

    for pattern in HIGH_RISK_PATTERNS:
        if pattern in normalized_clause:
            matched_patterns.append(pattern)
            return {
                "risk": "HIGH",
                "rule_score": 1.0,
                "matched_patterns": matched_patterns,
                "final_score": 1.0,
                "reason": "High-risk rule pattern matched.",
            }

    for pattern in MEDIUM_RISK_PATTERNS:
        if pattern in normalized_clause:
            matched_patterns.append(pattern)
            rule_score = 0.6
            final_score = rule_score * 0.5 + (1 - similarity_score) * 0.3 + anomaly_score * 0.2
            if final_score >= 0.7:
                risk = "HIGH"
            elif final_score >= 0.4:
                risk = "MEDIUM"
            else:
                risk = "LOW"
            return {
                "risk": risk,
                "rule_score": rule_score,
                "matched_patterns": matched_patterns,
                "final_score": final_score,
                "reason": "Medium-risk rule pattern matched.",
            }

    for pattern in LOW_RISK_PATTERNS:
        if pattern in normalized_clause:
            matched_patterns.append(pattern)
            break

    rule_score = 0.0
    final_score = rule_score * 0.5 + (1 - similarity_score) * 0.3 + anomaly_score * 0.2
    if final_score >= 0.7:
        risk = "HIGH"
    elif final_score >= 0.4:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "risk": risk,
        "rule_score": rule_score,
        "matched_patterns": matched_patterns,
        "final_score": final_score,
        "reason": "Risk determined by weighted similarity and anomaly scoring.",
    }


def analyze_risk(contract_data: list, standard_path: str = "data/processed/standard_clauses.json") -> list:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    model = _get_model()
    _load_standard_data(standard_path)

    if model is not None and _standard_indexes:
        print("⏳ Calibrating similarity thresholds...")
        all_similarities = []

        for clause in contract_data:
            clause_text = clean_clause(clause.get("text", ""))
            if not clause_text:
                continue

            predicted_type = classify_clause(clause_text)
            candidate_group = _standard_indexes.get(predicted_type)
            if candidate_group is None:
                continue

            clause_emb = np.array(_encode_clause(clause_text, model)).astype("float32").reshape(1, -1)
            _, indices = candidate_group["index"].search(clause_emb, k=1)
            matched_idx = int(indices[0][0])
            similarity = float(cosine_similarity(clause_emb, [candidate_group["embeddings"][matched_idx]])[0][0])
            all_similarities.append(similarity)

        HIGH_THRESH = float(np.percentile(all_similarities, 25)) if all_similarities else 0.60
        MED_THRESH = float(np.percentile(all_similarities, 50)) if all_similarities else 0.75
        print(f"✅ HIGH < {HIGH_THRESH:.3f} | MEDIUM < {MED_THRESH:.3f}")
    else:
        HIGH_THRESH = 0.60
        MED_THRESH = 0.75
        print("⚠️ Similarity calibration skipped because embeddings are unavailable.")

    results = []

    for clause in contract_data:
        clause_text = clean_clause(clause.get("text", ""))
        if not clause_text:
            continue

        predicted_type = classify_clause(clause_text)
        candidate_group = _standard_indexes.get(predicted_type)

        similarity = 0.0
        matched_clause = None
        clause_type = predicted_type
        clause_emb = None
        anomaly_score = 0.0

        if model is not None and candidate_group is not None:
            clause_emb = np.array(_encode_clause(clause_text, model)).astype("float32").reshape(1, -1)
            _, indices = candidate_group["index"].search(clause_emb, k=1)
            matched_idx = int(indices[0][0])
            matched_clause = candidate_group["items"][matched_idx]
            similarity = float(cosine_similarity(clause_emb, [candidate_group["embeddings"][matched_idx]])[0][0])
            clause_type = matched_clause.get("clause_type", predicted_type)

        if _iso_forest is not None and clause_emb is not None:
            raw_score = _iso_forest.score_samples(clause_emb)[0]
            anomaly_score = float(1 / (1 + np.exp(5 * raw_score)))

        rule_result = evaluate_clause_risk(
            clause_text=clause_text,
            similarity_score=float(similarity),
            anomaly_score=float(anomaly_score),
            matched_clause=matched_clause,
        )

        rule_score = rule_result["rule_score"]
        combined_risk = rule_result["final_score"]
        risk = rule_result["risk"]

        if similarity >= MIN_SIMILARITY and matched_clause is not None:
            matched_standard_clause = matched_clause["text"]
        else:
            matched_standard_clause = None
            clause_type = predicted_type if clause_type == "Unknown" else clause_type

        results.append({
            "contract_clause": clause_text,
            "matched_standard_clause": matched_standard_clause,
            "clause_type": clause_type,
            "similarity_score": float(similarity),
            "anomaly_score": float(anomaly_score),
            "combined_risk_score": float(combined_risk),
            "risk_level": risk,
            "rule_score": float(rule_score),
            "rule_triggered": bool(rule_result["matched_patterns"]),
            "matched_patterns": rule_result["matched_patterns"],
            "rule_reason": rule_result["reason"],
        })

    total = len(results)
    high = sum(1 for r in results if r["risk_level"] == "HIGH")
    medium = sum(1 for r in results if r["risk_level"] == "MEDIUM")
    low = sum(1 for r in results if r["risk_level"] == "LOW")

    print("\n📊 Risk Summary:")
    print(f"   Total  : {total}")
    print(f"   HIGH   : {high}")
    print(f"   MEDIUM : {medium}")
    print(f"   LOW    : {low}")

    return results


def save_risk_results(results: list, output_path: str = "data/processed/industry_risk_analysis.json") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print(f"✅ Risk results saved: {output_path}")
    return output_path


def load_risk_results(path: str = "data/processed/industry_risk_analysis.json") -> list:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  
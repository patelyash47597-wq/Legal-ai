"""
app/services/explainer.py
Generates conservative AI explanations for risky clauses.
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except ImportError:  # pragma: no cover - environment may not include Groq SDK
    Groq = None

MIN_SIMILARITY = 0.50

_client = None


def _get_client():
    global _client
    if _client is None:
        if Groq is None:
            print("⚠️  Groq SDK not available - AI explanations will be disabled")
            return None
        
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            print("⚠️  GROQ_API_KEY not set - AI explanations will be disabled")
            print("   Set GROQ_API_KEY on Render Dashboard → Settings → Environment")
            print("   Get it from: https://console.groq.com/api-keys")
            return None
        
        try:
            _client = Groq(api_key=api_key)
        except Exception as e:
            print(f"⚠️  Failed to initialize Groq client: {e}")
            return None
    return _client


def build_safe_explanation(
    clause: str,
    matched_standard_clause: str | None,
    similarity_score: float | None,
    anomaly_score: float | None,
    risk_level: str,
    clause_type: str = "Unknown",
) -> str:
    """Builds a conservative explanation that does not invent missing legal facts."""

    if risk_level not in ["HIGH", "MEDIUM"]:
        return "Clause aligns with approved standards. No significant risk identified."

    similarity = float(similarity_score or 0.0)
    if not matched_standard_clause or similarity < MIN_SIMILARITY:
        return (
            "No sufficiently similar standard clause was found. "
            "Evidence is insufficient for a detailed comparison. "
            "This explanation relies only on the incoming clause and the available evidence. "
            "Risk is based mainly on anomaly detection because the clause could not be matched confidently. "
            "No specific financial terms, deadlines, penalties, or legal consequences were inferred."
        )

    return (
        "The clause was compared to a relevant standard clause. "
        "The explanation uses only the incoming clause and the matched standard clause. "
        "No payment terms, deadlines, penalties, or legal consequences were inferred."
    )


def explain_clause(
    clause: str,
    standard: str,
    risk: str,
    similarity_score: float | None = None,
    anomaly_score: float | None = None,
    clause_type: str = "Unknown",
) -> str:
    """Generates a short explanation for a clause while avoiding hallucinations."""

    if risk not in ["HIGH", "MEDIUM"]:
        return "Clause aligns with approved standards. No significant risk identified."

    if not standard or (similarity_score is not None and similarity_score < MIN_SIMILARITY):
        return build_safe_explanation(
            clause=clause,
            matched_standard_clause=standard,
            similarity_score=similarity_score,
            anomaly_score=anomaly_score,
            risk_level=risk,
            clause_type=clause_type,
        )

    client = _get_client()
    if client is None:
        return build_safe_explanation(
            clause=clause,
            matched_standard_clause=standard,
            similarity_score=similarity_score,
            anomaly_score=anomaly_score,
            risk_level=risk,
            clause_type=clause_type,
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a legal AI assistant. Use only the incoming clause and the approved standard clause as evidence. "
                        "Do not invent payment terms, deadlines, penalties, legal consequences, or missing facts. "
                        "If evidence is insufficient, say so plainly. If risk is based mainly on anomaly detection, say that explicitly. Provide three short bullet points."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Incoming Clause:\n{clause}\n\n"
                        f"Approved Standard Clause:\n{standard}\n\n"
                        "Explain in 3 short bullets:\n"
                        "1. What appears different from the standard clause\n"
                        "2. Why the clause may be risky\n"
                        "3. What evidence is available and what is not, including when the explanation is based mainly on anomaly detection\n"
                        "Do not speculate beyond the provided texts or invent specific financial terms, deadlines, penalties, or legal consequences."
                    ),
                },
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"


# ----------------------------------------
# EXPLAIN ALL CLAUSES IN BATCH
# ----------------------------------------

def generate_explanations(risk_data: list) -> list:
    """Adds AI explanations to all clauses in risk_data."""

    total = len(risk_data)
    result = []

    for index, item in enumerate(risk_data, start=1):
        clause = item["contract_clause"]
        standard = item.get("matched_standard_clause")
        risk = item["risk_level"]
        similarity_score = item.get("similarity_score")
        anomaly_score = item.get("anomaly_score")
        clause_type = item.get("clause_type", "Unknown")

        print(f"🤖 Explaining {index}/{total} | Risk: {risk}")

        explanation = explain_clause(
            clause=clause,
            standard=standard,
            risk=risk,
            similarity_score=similarity_score,
            anomaly_score=anomaly_score,
            clause_type=clause_type,
        )

        item["ai_explanation"] = explanation
        result.append(item)

        print(f"   ✅ {explanation[:70]}...")

    return result


# ----------------------------------------
# SAVE FINAL RESULTS
# ----------------------------------------

def save_final_results(results: list, output_path: str = "data/processed/final_contract_analysis.json") -> str:
    """Saves final analysis with explanations to JSON."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"✅ Final results saved: {output_path}")
    return output_path


# ----------------------------------------
# LOAD EXISTING FINAL RESULTS
# ----------------------------------------

def load_final_results(path: str = "data/processed/final_contract_analysis.json") -> list:
    """Loads existing final analysis from disk."""

    if not os.path.exists(path):
        raise FileNotFoundError(f"Final results not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
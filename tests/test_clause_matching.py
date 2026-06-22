from app.services.industry_clause_engine import clean_clause, classify_clause_type
from app.services.explainer import build_safe_explanation
from app.services.risk_engine import evaluate_clause_risk


def test_classify_clause_type_detects_payment_language():
    clause = "The customer shall pay all invoices within 30 days of receipt."
    assert classify_clause_type(clause) == "Payment"


def test_classify_clause_type_detects_confidentiality_language():
    clause = "Each party shall keep confidential information secret and not disclose it."
    assert classify_clause_type(clause) == "Confidentiality"


def test_safe_explanation_handles_no_sufficient_match():
    explanation = build_safe_explanation(
        clause="EMPLOYEE NAME and ADDRESS are listed on the form.",
        matched_standard_clause=None,
        similarity_score=0.37,
        anomaly_score=0.82,
        risk_level="HIGH",
        clause_type="Unknown",
    )
    assert "No sufficiently similar standard clause was found." in explanation
    assert "anomaly detection" in explanation.lower()
    assert "payment" not in explanation.lower()


def test_clean_clause_filters_headings_and_metadata():
    assert clean_clause("1. Definition of Confidential Information.") is None
    assert clean_clause("Copyright © 2020 NonDisclosureAgreement.com.") is None
    assert clean_clause("Typed or Printed Name:") is None
    assert clean_clause("The receiving party shall protect confidential information and use it only for authorized purposes.") is not None


def test_classify_clause_type_detects_definition_language():
    clause = "For purposes of this Agreement, Confidential Information means nonpublic business information."
    assert classify_clause_type(clause) == "Definition"


def test_evaluate_clause_risk_flags_high_risk_pattern_even_with_high_similarity():
    result = evaluate_clause_risk(
        clause_text="The Receiving Party may share confidential information with any third party without obtaining prior consent.",
        similarity_score=0.85,
        anomaly_score=0.10,
    )
    assert result["risk"] == "HIGH"
    assert result["rule_score"] == 1.0
    assert result["matched_patterns"]

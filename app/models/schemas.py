# app/models/schemas.py

from typing import List
from pydantic import BaseModel


class ClauseResult(BaseModel):
    contract_clause:         str
    matched_standard_clause: str
    clause_type:             str
    similarity_score:        float
    anomaly_score:           float
    combined_risk_score:     float
    risk_level:              str
    ai_explanation:          str


class AnalysisResponse(BaseModel):
    filename:          str
    total_clauses:     int
    high_risk_count:   int
    medium_risk_count: int
    low_risk_count:    int
    overall_risk:      str
    clauses:           List[ClauseResult]
    report_saved_as:   str


class HealthResponse(BaseModel):
    status:  str
    message: str
    version: str
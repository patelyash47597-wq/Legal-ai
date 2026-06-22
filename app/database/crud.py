"""
app/database/crud.py
All database CRUD operations.
Called from routes.py after pipeline completes.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import (
    Contract,
    Clause,
    RiskResult,
    AnalysisReport
)


# ----------------------------------------
# CONTRACT CRUD
# ----------------------------------------

def create_contract(
    db: Session,
    filename: str,
    original_name: str,
    file_path: str,
    file_size: int = None
) -> Contract:
    """Creates a new contract record."""

    contract = Contract(
        filename      = filename,
        original_name = original_name,
        file_path     = file_path,
        file_size     = file_size,
        status        = "processing"
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract_status(
    db: Session,
    contract_id: int,
    status: str
) -> Contract:
    """Updates contract processing status."""

    contract = db.query(Contract).filter(
        Contract.id == contract_id
    ).first()

    if contract:
        contract.status = status
        db.commit()
        db.refresh(contract)

    return contract


def get_contract_by_id(
    db: Session,
    contract_id: int
) -> Contract:
    """Gets contract by ID."""

    return db.query(Contract).filter(
        Contract.id == contract_id
    ).first()


def get_all_contracts(db: Session) -> list:
    """Gets all contracts."""

    return db.query(Contract).order_by(
        Contract.uploaded_at.desc()
    ).all()


# ----------------------------------------
# CLAUSE CRUD
# ----------------------------------------

def create_clauses_bulk(
    db: Session,
    contract_id: int,
    clauses: list
) -> list:
    """
    Bulk inserts all clauses for a contract.
    Much faster than inserting one by one.
    """

    clause_objects = [
        Clause(
            contract_id = contract_id,
            clause_id   = c.get("clause_id", i + 1),
            text        = c["text"],
            length      = c.get("length", len(c["text"])),
            word_count  = c.get("word_count", len(c["text"].split()))
        )
        for i, c in enumerate(clauses)
    ]

    db.bulk_save_objects(clause_objects, return_defaults=True)
    db.commit()

    # Reload to get IDs
    saved = db.query(Clause).filter(
        Clause.contract_id == contract_id
    ).order_by(Clause.clause_id).all()

    return saved


def get_clauses_by_contract(
    db: Session,
    contract_id: int
) -> list:
    """Gets all clauses for a contract."""

    return db.query(Clause).filter(
        Clause.contract_id == contract_id
    ).order_by(Clause.clause_id).all()


# ----------------------------------------
# RISK RESULT CRUD
# ----------------------------------------

def create_risk_results_bulk(
    db: Session,
    clause_db_objects: list,
    risk_results: list
) -> None:
    """
    Bulk inserts risk results linked to clause DB objects.

    Args:
        clause_db_objects: Clause ORM objects (with DB ids)
        risk_results:      Risk analysis dicts from risk_engine
    """

    risk_objects = []

    for i, result in enumerate(risk_results):

        # Link to DB clause if available
        clause_db_id = (
            clause_db_objects[i].id
            if i < len(clause_db_objects)
            else None
        )

        risk_obj = RiskResult(
            clause_id               = clause_db_id,
            contract_clause         = result["contract_clause"],
            matched_standard_clause = result.get("matched_standard_clause", ""),
            clause_type             = result.get("clause_type", "General"),
            similarity_score        = result.get("similarity_score", 0.0),
            anomaly_score           = result.get("anomaly_score", 0.0),
            combined_risk_score     = result.get("combined_risk_score", 0.0),
            risk_level              = result["risk_level"],
            ai_explanation          = result.get("ai_explanation", "")
        )
        risk_objects.append(risk_obj)

    db.bulk_save_objects(risk_objects)
    db.commit()
    print(f"✅ {len(risk_objects)} risk results saved to MySQL")


def get_risk_results_by_contract(
    db: Session,
    contract_id: int
) -> list:
    """Gets all risk results for a contract via clause join."""

    return (
        db.query(RiskResult)
        .join(Clause, RiskResult.clause_id == Clause.id)
        .filter(Clause.contract_id == contract_id)
        .all()
    )


# ----------------------------------------
# ANALYSIS REPORT CRUD
# ----------------------------------------

def create_analysis_report(
    db: Session,
    contract_id: int,
    total_clauses: int,
    high_risk_count: int,
    medium_risk_count: int,
    low_risk_count: int,
    overall_risk: str,
    report_filename: str
) -> AnalysisReport:
    """Creates analysis report summary."""

    report = AnalysisReport(
        contract_id       = contract_id,
        total_clauses     = total_clauses,
        high_risk_count   = high_risk_count,
        medium_risk_count = medium_risk_count,
        low_risk_count    = low_risk_count,
        overall_risk      = overall_risk,
        report_filename   = report_filename
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    print(f"✅ Analysis report saved to MySQL (id={report.id})")
    return report


def get_report_by_contract(
    db: Session,
    contract_id: int
) -> AnalysisReport:
    """Gets analysis report for a contract."""

    return db.query(AnalysisReport).filter(
        AnalysisReport.contract_id == contract_id
    ).first()


def get_all_reports(db: Session) -> list:
    """Gets all analysis reports."""

    return db.query(AnalysisReport).order_by(
        AnalysisReport.created_at.desc()
    ).all()
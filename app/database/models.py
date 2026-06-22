"""
app/database/models.py
SQLAlchemy ORM models — defines all MySQL tables.

Tables:
  1. contracts       → uploaded PDF info
  2. clauses         → extracted clauses per contract
  3. risk_results    → risk analysis per clause
  4. analysis_reports → final report summary
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.orm import relationship
from app.database.database import Base


# ----------------------------------------
# TABLE 1: CONTRACTS
# Stores uploaded PDF info
# ----------------------------------------

class Contract(Base):

    __tablename__ = "contracts"

    id            = Column(Integer, primary_key=True, index=True)
    filename      = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path     = Column(String(500), nullable=False)
    file_size     = Column(Integer, nullable=True)
    uploaded_at   = Column(DateTime, default=datetime.utcnow)
    status        = Column(
        String(50),
        default="pending"   # pending / processing / completed / failed
    )

    # Relationships
    clauses = relationship(
        "Clause",
        back_populates="contract",
        cascade="all, delete-orphan"
    )
    report = relationship(
        "AnalysisReport",
        back_populates="contract",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Contract id={self.id} file={self.filename}>"


# ----------------------------------------
# TABLE 2: CLAUSES
# Stores each extracted clause
# ----------------------------------------

class Clause(Base):

    __tablename__ = "clauses"

    id          = Column(Integer, primary_key=True, index=True)
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    clause_id   = Column(Integer, nullable=False)   # sequence in doc
    text        = Column(Text, nullable=False)
    length      = Column(Integer, nullable=True)
    word_count  = Column(Integer, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contract    = relationship("Contract", back_populates="clauses")
    risk_result = relationship(
        "RiskResult",
        back_populates="clause",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Clause id={self.id} contract_id={self.contract_id}>"


# ----------------------------------------
# TABLE 3: RISK RESULTS
# Stores risk analysis for each clause
# ----------------------------------------

class RiskResult(Base):

    __tablename__ = "risk_results"

    id                      = Column(Integer, primary_key=True, index=True)
    clause_id               = Column(
        Integer,
        ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contract_clause         = Column(Text, nullable=False)
    matched_standard_clause = Column(Text, nullable=True)
    clause_type             = Column(String(100), nullable=True)
    similarity_score        = Column(Float, nullable=True)
    anomaly_score           = Column(Float, nullable=True)
    combined_risk_score     = Column(Float, nullable=True)
    risk_level              = Column(
        Enum("HIGH", "MEDIUM", "LOW"),
        nullable=False,
        index=True
    )
    ai_explanation          = Column(Text, nullable=True)
    created_at              = Column(DateTime, default=datetime.utcnow)

    # Relationship
    clause = relationship("Clause", back_populates="risk_result")

    def __repr__(self):
        return f"<RiskResult id={self.id} risk={self.risk_level}>"


# ----------------------------------------
# TABLE 4: ANALYSIS REPORTS
# Stores summary of full contract analysis
# ----------------------------------------

class AnalysisReport(Base):

    __tablename__ = "analysis_reports"

    id                = Column(Integer, primary_key=True, index=True)
    contract_id       = Column(
        Integer,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    total_clauses     = Column(Integer, nullable=False)
    high_risk_count   = Column(Integer, default=0)
    medium_risk_count = Column(Integer, default=0)
    low_risk_count    = Column(Integer, default=0)
    overall_risk      = Column(
        Enum("HIGH", "MEDIUM", "LOW"),
        nullable=False
    )
    report_filename   = Column(String(255), nullable=True)
    created_at        = Column(DateTime, default=datetime.utcnow)

    # Relationship
    contract = relationship("Contract", back_populates="report")

    def __repr__(self):
        return (
            f"<AnalysisReport id={self.id} "
            f"overall={self.overall_risk}>"
        )
"""
app/api/routes.py - All API endpoints with MySQL integration.
"""
import json
import os
import shutil
import traceback
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.schemas import HealthResponse
from app.database.database import get_db
from app.database import crud

router = APIRouter()

RAW_DIR       = "data/raw"
PROCESSED_DIR = "data/processed"
UPLOADS_DIR   = "data/uploads"

for d in [RAW_DIR, PROCESSED_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

def _load_json(path):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(status="healthy", message="Legal AI API running ✅", version="1.0.0")

@router.post("/analyze", tags=["Analysis"])
async def analyze_contract(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")

    upload_path = os.path.join(UPLOADS_DIR, file.filename)
    content     = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    contract_db = crud.create_contract(db=db, filename=file.filename,
        original_name=file.filename, file_path=upload_path, file_size=len(content))
    print(f"✅ Contract saved to MySQL (id={contract_db.id})")

    try:
        from app.services.parser import parse_pdf, save_contract_json
        contract_data = parse_pdf(upload_path)
        save_contract_json(contract_data, f"{PROCESSED_DIR}/contract.json")
        text = contract_data["text"]
    except Exception as e:
        traceback.print_exc()
        crud.update_contract_status(db, contract_db.id, "failed")
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")

    try:
        from app.services.industry_clause_engine import extract_clauses, save_clauses
        clauses = extract_clauses(text)
        save_clauses(clauses, f"{PROCESSED_DIR}/industry_clauses.json")
    except Exception as e:
        traceback.print_exc()
        crud.update_contract_status(db, contract_db.id, "failed")
        raise HTTPException(status_code=500, detail=f"Clause extraction failed: {e}")

    clause_db_objects = crud.create_clauses_bulk(db=db, contract_id=contract_db.id, clauses=clauses)
    print(f"✅ {len(clause_db_objects)} clauses saved to MySQL")

    try:
        from app.services.risk_engine import analyze_risk, save_risk_results
        risk_results = analyze_risk(clauses, standard_path=f"{PROCESSED_DIR}/standard_clauses.json")
        save_risk_results(risk_results, f"{PROCESSED_DIR}/industry_risk_analysis.json")
    except Exception as e:
        traceback.print_exc()
        crud.update_contract_status(db, contract_db.id, "failed")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")

    try:
        from app.services.explainer import generate_explanations, save_final_results
        final_results   = generate_explanations(risk_results)
        report_filename = file.filename.replace(".pdf", "_report.json")
        save_final_results(final_results, f"{PROCESSED_DIR}/{report_filename}")
        save_final_results(final_results, f"{PROCESSED_DIR}/final_contract_analysis.json")
    except Exception as e:
        traceback.print_exc()
        crud.update_contract_status(db, contract_db.id, "failed")
        raise HTTPException(status_code=500, detail=f"AI explanation failed: {e}")

    crud.create_risk_results_bulk(db=db, clause_db_objects=clause_db_objects, risk_results=final_results)

    risk_levels  = [r["risk_level"] for r in final_results]
    overall_risk = "HIGH" if "HIGH" in risk_levels else "MEDIUM" if "MEDIUM" in risk_levels else "LOW"

    crud.create_analysis_report(db=db, contract_id=contract_db.id,
        total_clauses=len(final_results), high_risk_count=risk_levels.count("HIGH"),
        medium_risk_count=risk_levels.count("MEDIUM"), low_risk_count=risk_levels.count("LOW"),
        overall_risk=overall_risk, report_filename=report_filename)

    crud.update_contract_status(db, contract_db.id, "completed")
    print("✅ All data saved to MySQL!")

    return {"contract_db_id": contract_db.id, "filename": file.filename,
        "total_clauses": len(final_results), "high_risk_count": risk_levels.count("HIGH"),
        "medium_risk_count": risk_levels.count("MEDIUM"), "low_risk_count": risk_levels.count("LOW"),
        "overall_risk": overall_risk, "clauses": final_results, "report_saved_as": report_filename}

@router.get("/contracts", tags=["MySQL Data"])
async def get_all_contracts(db: Session = Depends(get_db)):
    try:
        contracts = crud.get_all_contracts(db)
        return {"total": len(contracts), "contracts": [
            {"id": c.id, "filename": c.filename, "file_size": c.file_size,
             "status": c.status, "uploaded_at": str(c.uploaded_at)} for c in contracts]}
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not load contracts from the database.",
        ) from exc

@router.get("/contracts/{contract_id}/results", tags=["MySQL Data"])
async def get_contract_results(contract_id: int, db: Session = Depends(get_db)):
    contract = crud.get_contract_by_id(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract id={contract_id} not found")
    results = crud.get_risk_results_by_contract(db, contract_id)
    return {"contract_id": contract_id, "filename": contract.filename, "total": len(results),
        "results": [{"id": r.id, "contract_clause": r.contract_clause,
            "matched_standard_clause": r.matched_standard_clause, "clause_type": r.clause_type,
            "similarity_score": r.similarity_score, "anomaly_score": r.anomaly_score,
            "combined_risk_score": r.combined_risk_score, "risk_level": r.risk_level,
            "ai_explanation": r.ai_explanation} for r in results]}

@router.get("/reports/all", tags=["MySQL Data"])
async def get_all_reports_db(db: Session = Depends(get_db)):
    try:
        reports = crud.get_all_reports(db)
        return {"total": len(reports), "reports": [
            {"id": r.id, "contract_id": r.contract_id, "total_clauses": r.total_clauses,
             "high_risk_count": r.high_risk_count, "medium_risk_count": r.medium_risk_count,
             "low_risk_count": r.low_risk_count, "overall_risk": r.overall_risk,
             "report_filename": r.report_filename, "created_at": str(r.created_at)} for r in reports]}
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not load reports from the database.",
        ) from exc

@router.get("/report", tags=["JSON Files"])
async def get_default_report():
    return JSONResponse(content=_load_json(f"{PROCESSED_DIR}/final_contract_analysis.json"))

@router.get("/reports", tags=["JSON Files"])
async def list_reports():
    try:
        files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]
        return {"total": len(files), "reports": sorted(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
# Import the GARDA-JKN LangGraph agent
from app.agents.workflow import garda_app


# --- Models ---
class ClaimData(BaseModel):
    model_config = ConfigDict(extra="allow")

    id_kunjungan: str
    nama_pasien: str
    nik: str
    usia: int
    diag_awal: str
    diag_sekunder_1: Optional[str] = None
    diag_sekunder_2: Optional[str] = None
    tindakan_1: Optional[str] = None
    tindakan_2: Optional[str] = None
    icu_days: int
    severity_level: int
    biaya_tagih: float
    durasi_rawat: int
    # Optional clinical & administrative indicators for validator rules
    catatan_klinis: Optional[str] = None
    kreatinin: Optional[float] = None
    troponin: Optional[float] = None
    tipe_faskes: Optional[str] = None
    eeg_attached: Optional[bool] = None


class EvaluationDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: str
    adjudication_result: str
    severity_level: int
    confidence_score: float
    ml_risk_score: float
    is_anomalous: bool
    reason_codes: List[str] = []
    adjudication_reason: str = ""
    rag_context: str = ""


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool
    metadata: dict
    response: EvaluationDetail
    adjudication_result: Optional[str] = None
    severity_level: Optional[int] = None
    confidence_score: Optional[float] = None


# --- Application Setup ---
app = FastAPI(title="GARDA-JKN Evaluator API", description="AI Adjudicator for BPJS Claims")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon; restrict to frontend domain in prod
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "GARDA-JKN API is running."}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "GARDA-JKN API"}


@app.post("/api/v1/adjudicate", response_model=EvaluationResponse)
def adjudicate_claim(claim: ClaimData):
    try:
        # Convert pydantic model to dict
        claim_dict = claim.model_dump()  # Updated for Pydantic V2

        # Run LangGraph AI Workflow
        initial_state = {"claim_data": claim_dict}
        final_state = garda_app.invoke(initial_state)

        # Extract adjudication outcomes
        decision = final_state.get("final_status", "UNKNOWN")
        raw_sev = final_state.get("revised_severity_level") or claim_dict.get("severity_level", 1)
        try:
            severity = int(raw_sev)
        except (ValueError, TypeError):
            severity = 1
        confidence = float(final_state.get("confidence_score", 0.95))
        ml_risk = float(final_state.get("ml_risk_score", 0.0))
        is_anom = bool(final_state.get("is_anomalous", False))
        ml_explanation = final_state.get("ml_explanation", "")
        reason_codes = [ml_explanation] if ml_explanation else []
        adj_reason = final_state.get("adjudication_reason", "")
        rag_ctx = final_state.get("rag_context", "")

        response_detail = {
            "decision": decision,
            "adjudication_result": decision,
            "severity_level": severity,
            "confidence_score": confidence,
            "ml_risk_score": ml_risk,
            "is_anomalous": is_anom,
            "reason_codes": reason_codes,
            "adjudication_reason": adj_reason,
            "rag_context": rag_ctx
        }

        # Build response to match both frontend (response.response.decision)
        # and acceptance criteria (adjudication_result, severity_level, confidence_score)
        return {
            "success": True,
            "metadata": {
                "code": 200,
                "message": "Evaluasi Selesai"
            },
            "response": response_detail,
            "adjudication_result": decision,
            "severity_level": severity,
            "confidence_score": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

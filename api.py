from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

# Import the GARDA-JKN LangGraph agent
from app.agents.workflow import garda_app

# --- Models ---
class ClaimData(BaseModel):
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

class EvaluationResponse(BaseModel):
    success: bool
    metadata: dict
    response: dict

# --- Application Setup ---
app = FastAPI(title="GARDA-JKN Evaluator API", description="AI Adjudicator for BPJS Claims")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for hackathon; restrict to frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "GARDA-JKN API is running."}

@app.post("/api/v1/adjudicate", response_model=EvaluationResponse)
def adjudicate_claim(claim: ClaimData):
    try:
        # Convert pydantic model to dict
        claim_dict = claim.model_dump() # Updated for Pydantic V2
        
        # Run LangGraph AI Workflow
        initial_state = {"claim_data": claim_dict}
        final_state = garda_app.invoke(initial_state)
        
        # Build strict response to match frontend expectation
        return {
            "success": True,
            "metadata": {
                "code": 200,
                "message": "Evaluasi Selesai"
            },
            "response": {
                "decision": final_state.get("final_status", "UNKNOWN"),
                "ml_risk_score": final_state.get("ml_risk_score", 0.0),
                "is_anomalous": final_state.get("is_anomalous", False),
                "reason_codes": [final_state.get("ml_explanation", "")],
                "adjudication_reason": final_state.get("adjudication_reason", ""),
                "rag_context": final_state.get("rag_context", "")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import json
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional, List
# Import the GARDA-JKN LangGraph agent
from app.agents.workflow import garda_app
from app.agents.trace import evaluation_detail_from_state, iter_workflow_events
from app.core.rag_ingest import ingest_uploaded_document, list_ingested_documents


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
    reason_codes: List[str] = Field(default_factory=list)
    data_quality_flags: List[str] = Field(default_factory=list)
    adjudication_reason: str = ""
    rag_context: str = ""
    audit_trail: dict = Field(default_factory=dict)


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

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://garda-jkn.vercel.app",
    ).split(",")
    if origin.strip()
]

# Keep CORS explicit because claims contain personal and clinical data.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "GARDA-JKN API is running."}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "GARDA-JKN API"}


def _evaluation_response(claim_dict: Dict[str, Any], final_state: Dict[str, Any]) -> Dict[str, Any]:
    detail = evaluation_detail_from_state(final_state, claim_dict)
    decision = detail["decision"]
    return {
        "success": True,
        "metadata": {"code": 200, "message": "Evaluasi Selesai"},
        "response": detail,
        "adjudication_result": decision,
        "severity_level": detail["severity_level"],
        "confidence_score": detail["confidence_score"],
    }


@app.post("/api/v1/adjudicate/stream")
def adjudicate_stream(claim: ClaimData):
    """Stream safe workflow progress events for the reviewer console."""
    claim_dict = claim.model_dump()

    def events():
        for event in iter_workflow_events(claim_dict):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/v1/adjudicate", response_model=EvaluationResponse)
def adjudicate_claim(claim: ClaimData):
    try:
        # Convert pydantic model to dict
        claim_dict = claim.model_dump()  # Updated for Pydantic V2

        # Run LangGraph AI Workflow
        initial_state = {"claim_data": claim_dict}
        final_state = garda_app.invoke(initial_state)

        return _evaluation_response(claim_dict, final_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/rag/documents")
def rag_documents():
    """List local RAG manifest metadata without returning document contents."""
    return {"documents": list_ingested_documents()}


@app.post("/api/v1/rag/documents")
async def upload_rag_document(
    file: UploadFile = File(...),
    authority: str = Form(...),
    effective_date: str = Form(...),
    disease: str = Form(""),
    icd10: str = Form(""),
    rule_type: str = Form(""),
):
    """Upload and index one local medical reference document."""
    try:
        content = await file.read()
        record = ingest_uploaded_document(
            content,
            file.filename or "document",
            authority=authority,
            effective_date=effective_date,
            disease=disease,
            icd10=icd10,
            rule_type=rule_type,
        )
        return {"success": True, "document": record}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RAG ingestion failed") from exc

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import logging

from app.agents.workflow import garda_app

app = FastAPI(title="GARDA-JKN Microservice API", version="1.0.0")

class ClaimPayload(BaseModel):
    claim_data: Dict[str, Any]

@app.post("/api/v1/adjudicate-claim")
async def adjudicate_claim(payload: ClaimPayload):
    try:
        initial_state = {"claim_data": payload.claim_data}
        final_state = garda_app.invoke(initial_state)
        
        return {
            "status": "success",
            "decision": final_state.get("final_status", "UNKNOWN"),
            "adjudication_reason": final_state.get("adjudication_reason", ""),
            "ml_risk_score": final_state.get("ml_risk_score", 0.0),
            "ml_explanation": final_state.get("ml_explanation", ""),
            "is_anomalous": final_state.get("is_anomalous", False),
            "rag_context": final_state.get("rag_context", "")
        }
    except Exception as e:
        logging.error(f"Error in API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

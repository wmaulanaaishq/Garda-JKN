import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm import get_llm
from app.core.ml_engine import MLEngine
from app.core.vector_db import MedicalKnowledgeBase
from app.agents.state import ClaimState

llm = get_llm()
ml_engine = MLEngine()
kb = MedicalKnowledgeBase()

def intake_node(state: ClaimState) -> Dict[str, Any]:
    """Node 1: Intake & Preprocessing (Data Masking)"""
    print("➡️ [Intake Agent] Menerima klaim dan melakukan Data Masking...")
    claim_data = state["claim_data"].copy()
    
    # Masking Data Pribadi (Sesuai Blueprint: Zero-Knowledge Payload)
    masked_claim = claim_data.copy()
    if "nama_pasien" in masked_claim:
        masked_claim["nama_pasien"] = "[DISENSOR_UNTUK_PRIVASI]"
    if "nik" in masked_claim:
        masked_claim["nik"] = "[DISENSOR]"
        
    return {"claim_data": masked_claim}

def ml_scoring_node(state: ClaimState) -> Dict[str, Any]:
    """Node 2: Machine Learning Lapis 1 (XGBoost)"""
    print("➡️ [ML Agent] Menganalisis anomali statistik dengan XGBoost...")
    claim_data = state["claim_data"]
    
    # Deteksi anomali
    is_anomaly, risk_score, shap_explanation = ml_engine.predict_fraud(claim_data)
    
    return {
        "ml_risk_score": risk_score,
        "is_anomalous": is_anomaly,
        "ml_explanation": shap_explanation
    }

def rag_reasoning_node(state: ClaimState) -> Dict[str, Any]:
    """Node 3: Reasoning (Qdrant RAG)"""
    print("➡️ [Reasoning Agent] Menarik aturan PNPK dari Qdrant...")
    claim_data = state["claim_data"]
    
    # Jika tidak anomali dari XGBoost, bisa dilewati (tapi kita cek semua untuk demo)
    query = f"Aturan untuk diagnosis {claim_data.get('diag_awal', '')} dan tindakan {claim_data.get('tindakan_1', '')}"
    rag_context = kb.search_rules(query)
    
    return {"rag_context": rag_context}

def arbiter_node(state: ClaimState) -> Dict[str, Any]:
    """Node 4: Arbiter Agent (Hakim LLM DeepSeek-R1)"""
    print("➡️ [Arbiter Agent] Memutuskan hasil adjudikasi menggunakan DeepSeek-R1...")
    
    prompt = f"""
Anda adalah Hakim Adjudikasi GARDA-JKN (Generative Agent for Risk Detection and Adjudication).
Tugas Anda adalah memeriksa klaim asuransi kesehatan BPJS dan mendeteksi UPCODING atau PHANTOM BILLING.

DATA KLAIM (Masked):
{json.dumps(state['claim_data'], indent=2)}

HASIL MACHINE LEARNING (Lapis 1):
- Indikasi Anomali: {state['is_anomalous']}
- Skor Risiko: {state.get('ml_risk_score', 0)}
- Penjelasan SHAP: {state.get('ml_explanation', '')}

REFERENSI MEDIS (PNPK / Aturan RAG Lapis 2):
{state.get('rag_context', 'Tidak ada referensi.')}

TUGAS:
Berikan keputusan adjudikasi secara tegas dan klinis.
Pilihan Status: APPROVED, DOWNGRADED (jika terbukti upcoding), ESCALATED (jika ambigu).
Gunakan format JSON:
{{
    "status": "...",
    "rasionalisasi": "penjelasan medis singkat..."
}}
"""
    try:
        response = llm.invoke([SystemMessage(content="Keluarkan hanya format JSON murni."), HumanMessage(content=prompt)])
        # Membersihkan string jika model memberikan markdown block
        clean_json = response.content.replace('```json', '').replace('```', '').strip()
        decision = json.loads(clean_json)
        status = decision.get("status", "ESCALATED")
        reasoning = decision.get("rasionalisasi", "Gagal memparsing alasan.")
    except Exception as e:
        status = "ESCALATED"
        reasoning = f"Sistem AI gagal memberikan keputusan: {str(e)}"

    return {
        "final_status": status,
        "adjudication_reason": reasoning
    }

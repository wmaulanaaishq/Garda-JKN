from typing import TypedDict, List, Dict, Any, Optional

class ClaimState(TypedDict):
    """
    State (memori) yang dibawa melintasi berbagai agen selama proses adjudikasi.
    """
    claim_id: str
    patient_data: Dict[str, Any]
    clinical_data: Dict[str, Any]
    billing_data: Dict[str, Any]
    
    # Hasil Lapis 1 (Machine Learning)
    ml_risk_score: float
    ml_is_anomaly: bool
    
    # Hasil Lapis 2 & 3 (RAG & Multi-Agent)
    rag_references: List[str]          # Kutipan dokumen PNPK
    medical_validation_notes: str      # Analisa klinis dari Validator Agent
    is_upcoding_detected: bool         # Keputusan final Arbiter Agent
    revised_severity_level: Optional[int]
    
    # Laporan Akhir
    final_adjudication_letter: str
    status: str                        # "APPROVED", "REJECTED", "REVISED", "ESCALATED"

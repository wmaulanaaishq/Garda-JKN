"""GARDA-JKN Multi-Agent Claim Adjudication State Schema."""

from typing import Any, Dict, List, Optional, TypedDict


class AuditTrail(TypedDict, total=False):
    """Explainable AI audit trail breakdown for compliance and human verifikator review."""
    ml_risk_assessment: str
    pnpk_reference_rule: str
    clinical_inconsistency: str
    action_recommendation: str


class ClaimState(TypedDict, total=False):
    """State dictionary carried across all agent nodes in the LangGraph workflow."""

    # 1. Intake & PII-Masked Claim Payload
    claim_id: str
    claim_data: Dict[str, Any]
    patient_data: Dict[str, Any]          # Alias for backward compatibility
    clinical_data: Dict[str, Any]         # Alias for backward compatibility
    billing_data: Dict[str, Any]          # Alias for backward compatibility

    # 2. Lapis 1: Machine Learning Engine (XGBoost + SHAP)
    ml_risk_score: float
    is_anomalous: bool
    ml_is_anomaly: bool                   # Alias for backward compatibility
    ml_explanation: str
    analyzed_features: List[str]

    # 3. Lapis 2: Medical Knowledge Base (Qdrant RAG)
    rag_context: str
    rag_references: List[Dict[str, Any]]

    # 4. Lapis 3: Validator Agent ("Pengecek")
    validation_status: str                # "CLEAR", "DISCREPANCY_DETECTED", "AMBIGUOUS", "DATA_QUALITY_ERROR"
    preliminary_verdict: str              # "APPROVE_RECOMMENDED", "DOWNGRADE_RECOMMENDED", "ESCALATE_RECOMMENDED"
    clinical_inconsistencies: List[str]
    medical_validation_notes: str
    data_quality_flags: List[str]

    # 5. Lapis 4: Executor Agent ("Pengeksekusi" - LLM Arbiter)
    final_status: str                     # MANDATORY: "APPROVED" | "DOWNGRADED" | "ESCALATED"
    adjudication_reason: str              # MANDATORY: Formal Indonesian medical decision log
    confidence_score: float
    audit_trail: AuditTrail               # Explainable AI metrics (R3)

    # Aliases for UI & Legacy Compatibility
    status: str                           # Alias for final_status
    final_adjudication_letter: str         # Alias for adjudication_reason
    is_upcoding_detected: bool
    revised_severity_level: Optional[int]

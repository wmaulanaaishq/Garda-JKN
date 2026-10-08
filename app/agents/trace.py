"""Safe, structured execution tracing for the GARDA-JKN workflow.

The trace is intentionally an operational summary, not a dump of prompts or
private model reasoning. It is suitable for the reviewer UI and audit logs.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable

from app.agents.workflow import garda_app


NODE_LABELS = {
    "intake": "Intake & PII Masking",
    "ml_scoring": "ML Risk Scoring",
    "rag_retrieval": "RAG Retrieval",
    "validator": "Clinical Validator",
    "executor": "Adjudication Executor",
}


def evaluation_detail_from_state(state: Dict[str, Any], claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert internal graph state into the stable public response shape."""
    decision = state.get("final_status", "UNKNOWN")
    raw_severity = state.get("revised_severity_level") or claim_data.get("severity_level", 1)
    try:
        severity = int(raw_severity)
    except (TypeError, ValueError):
        severity = 1

    explanation = state.get("ml_explanation", "")
    return {
        "decision": decision,
        "adjudication_result": decision,
        "severity_level": severity,
        "confidence_score": float(state.get("confidence_score", 0.95)),
        "ml_risk_score": float(state.get("ml_risk_score", 0.0)),
        "is_anomalous": bool(state.get("is_anomalous", False)),
        "reason_codes": [explanation] if explanation else [],
        "data_quality_flags": state.get("data_quality_flags", []),
        "adjudication_reason": state.get("adjudication_reason", ""),
        "rag_context": state.get("rag_context", ""),
        "audit_trail": state.get("audit_trail", {}),
    }


def _summarize_node(node: str, update: Dict[str, Any]) -> Dict[str, Any]:
    """Return only non-sensitive, reviewer-useful fields for one node."""
    if node == "intake":
        claim = update.get("claim_data") or {}
        masked_fields = [
            key for key in ("nama_pasien", "nik", "nomor_kartu", "no_telepon", "alamat")
            if str(claim.get(key, "")).startswith("[") or "*" in str(claim.get(key, ""))
        ]
        return {"masked_fields": masked_fields, "claim_id_present": bool(update.get("claim_id"))}

    if node == "ml_scoring":
        return {
            "risk_score": round(float(update.get("ml_risk_score", 0.0)), 4),
            "is_anomalous": bool(update.get("is_anomalous", False)),
            "analyzed_features": update.get("analyzed_features", []),
        }

    if node == "rag_retrieval":
        references = update.get("rag_references") or []
        return {
            "reference_count": len(references),
            "sources": sorted({str(item.get("source", "")) for item in references if item.get("source")}),
        }

    if node == "validator":
        inconsistencies = update.get("clinical_inconsistencies") or []
        return {
            "validation_status": update.get("validation_status", "UNKNOWN"),
            "preliminary_verdict": update.get("preliminary_verdict", "UNKNOWN"),
            "inconsistency_count": len(inconsistencies),
            "data_quality_flags": update.get("data_quality_flags", []),
            "revised_severity_level": update.get("revised_severity_level"),
        }

    if node == "executor":
        return {
            "final_status": update.get("final_status", "UNKNOWN"),
            "confidence_score": round(float(update.get("confidence_score", 0.0)), 4),
            "has_audit_trail": bool(update.get("audit_trail")),
        }

    return {"updated_keys": sorted(update.keys())}


def iter_workflow_events(claim_data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield structured progress events and one final result event."""
    started = time.perf_counter()
    final_state: Dict[str, Any] = {}
    yield {"type": "run_started", "status": "running", "node": "workflow"}

    try:
        for chunk in garda_app.stream({"claim_data": claim_data}, stream_mode="updates"):
            updates = chunk.items() if isinstance(chunk, dict) else []
            for node, update in updates:
                if not isinstance(update, dict):
                    continue
                final_state.update(update)
                yield {
                    "type": "node_completed",
                    "status": "completed",
                    "node": node,
                    "label": NODE_LABELS.get(node, node),
                    "duration_ms": round((time.perf_counter() - started) * 1000),
                    "summary": _summarize_node(node, update),
                }

        yield {
            "type": "result",
            "status": "completed",
            "node": "workflow",
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "response": evaluation_detail_from_state(final_state, claim_data),
        }
    except Exception as exc:
        yield {
            "type": "run_error",
            "status": "failed",
            "node": "workflow",
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc),
        }

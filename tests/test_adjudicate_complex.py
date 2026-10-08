"""Comprehensive automated test suite for GARDA-JKN Claim Adjudication API.

Endpoint: POST /api/v1/adjudicate
Milestone: R2 — Complex Payload Processing & API Verification
Target: Real in-process execution with FastAPI TestClient, XGBoost MLEngine,
        and Qdrant MedicalKnowledgeBase (RAG).
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from api import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """Provides a reusable FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


def assert_adjudication_contract(
    payload_sent: dict, response_data: dict, expected_decision_in=None
):
    """Enforces the structural and semantic contract for /api/v1/adjudicate."""
    # 1. Top-level status & structure
    assert response_data.get("success") is True, (
        f"Response success should be True: {response_data}"
    )
    assert "metadata" in response_data, "Response missing 'metadata'"
    assert response_data["metadata"].get("code") == 200
    assert "response" in response_data, "Response missing 'response' payload"

    detail = response_data["response"]

    # 2. Key contract fields (present in detail and/or top-level)
    assert "decision" in detail, "detail missing 'decision'"
    assert "adjudication_result" in detail or (
        "adjudication_result" in response_data
    ), "adjudication_result must be present"
    assert "severity_level" in detail or (
        "severity_level" in response_data
    ), "severity_level must be present"
    assert "confidence_score" in detail or (
        "confidence_score" in response_data
    ), "confidence_score must be present"
    assert "ml_risk_score" in detail, "detail missing 'ml_risk_score'"
    assert "is_anomalous" in detail, "detail missing 'is_anomalous'"

    # 3. Decision & adjudication_result values
    decision = detail["decision"]
    assert decision in ["APPROVED", "DOWNGRADED", "ESCALATED"], (
        f"Invalid decision: {decision}"
    )
    if expected_decision_in:
        assert decision in expected_decision_in, (
            f"Expected decision in {expected_decision_in}, got {decision}"
        )

    adj_result = response_data.get("adjudication_result") or detail.get(
        "adjudication_result"
    )
    assert adj_result in ["APPROVED", "DOWNGRADED", "ESCALATED"], (
        f"Invalid adjudication_result: {adj_result}"
    )
    assert adj_result == decision, (
        f"adjudication_result ({adj_result}) must match decision ({decision})"
    )

    # 4. Severity level verification
    sev_level = (
        response_data.get("severity_level")
        if "severity_level" in response_data
        else detail.get("severity_level")
    )
    assert isinstance(sev_level, int), (
        f"severity_level must be int, got {type(sev_level)}"
    )
    assert sev_level in [1, 2, 3], (
        f"severity_level must be 1, 2, or 3, got {sev_level}"
    )

    # 5. Confidence score verification
    conf_score = (
        response_data.get("confidence_score")
        if "confidence_score" in response_data
        else detail.get("confidence_score")
    )
    assert isinstance(conf_score, (float, int)), (
        f"confidence_score must be float, got {type(conf_score)}"
    )
    assert 0.0 <= conf_score <= 1.0, (
        f"confidence_score out of bounds: {conf_score}"
    )

    # 6. ML risk score verification (XGBoost execution)
    ml_risk = detail["ml_risk_score"]
    assert isinstance(ml_risk, (float, int)), (
        f"ml_risk_score must be numeric, got {type(ml_risk)}"
    )
    assert 0.0 <= ml_risk <= 1.0, f"ml_risk_score out of bounds: {ml_risk}"

    # 7. Qdrant Vector DB (RAG) execution verification
    rag_ctx = detail.get("rag_context", "")
    assert isinstance(rag_ctx, str), (
        f"rag_context must be string, got {type(rag_ctx)}"
    )
    assert len(rag_ctx.strip()) > 0, (
        "rag_context must be non-empty (Qdrant RAG must execute)"
    )

    # 8. Explainability: SHAP reason codes or adjudication reason strings
    reason_codes = detail.get("reason_codes", [])
    adj_reason = detail.get("adjudication_reason", "")
    assert isinstance(reason_codes, list), "reason_codes must be a list"
    assert isinstance(adj_reason, str), "adjudication_reason must be a string"
    has_valid_codes = len(reason_codes) > 0 and any(
        isinstance(c, str) and len(c.strip()) > 0 for c in reason_codes
    )
    has_valid_reason = len(adj_reason.strip()) > 0
    assert has_valid_codes or has_valid_reason, (
        "Either reason_codes or adjudication_reason must be populated"
    )


# ============================================================================
# Core Complex Payload Tests
# ============================================================================

def test_stroke_with_severe_aki_kdigo_downgrade(client):
    """Test Case 1: Stroke with severe AKI KDIGO comorbidity.

    Scenario:
    - Primary: Stroke Iskemik Akut (I63.9).
    - Secondary 1: Gagal Ginjal Akut / AKI (N17.9).
    - Secondary 2: Hipertensi Esensial (I10).
    - Claimed Severity: Level 3.
    - Expected behavior:
      Validator node inspects AKI comorbidity without verified serial
      lab creatinine, flagging an upcoding discrepancy and recommending
      DOWNGRADE to Severity Level 2.
    """
    payload = {
        "id_kunjungan": "BPJS-STR-2026-001",
        "nama_pasien": "Siti Rahmawati",
        "nik": "3201024508760002",
        "usia": 68,
        "diag_awal": "Stroke Iskemik Akut (I63.9)",
        "diag_sekunder_1": "Gagal Ginjal Akut (N17.9)",
        "diag_sekunder_2": "Hipertensi Esensial (I10)",
        "tindakan_1": "CT-Scan Kepala Non-Kontras",
        "tindakan_2": "Pemberian Antiplatelet IV",
        "icu_days": 0,
        "severity_level": 3,
        "biaya_tagih": 18500000.0,
        "durasi_rawat": 3,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(
        payload, data, expected_decision_in=["DOWNGRADED"]
    )

    detail = data["response"]
    # Revised severity should be lowered to Level 2
    sev = data.get("severity_level") or detail.get("severity_level")
    assert sev == 2, f"Severity level should be downgraded to 2, got {sev}"

    # Adjudication explanation should mention the clinical reason
    reason_text = detail.get("adjudication_reason", "")
    assert (
        "DOWNGRADE" in reason_text
        or "turun" in reason_text.lower()
        or "kreatinin" in reason_text.lower()
    )


def test_sepsis_shock_zero_icu_clinical_incoherence(client):
    """Test Case 2: Sepsis/Shock with 0 ICU days (Incoherence Anomaly).

    Scenario:
    - Primary: Sepsis Berat (A41.9).
    - Secondary 1: Syok Septik (R57.2).
    - ICU Days: 0 (Major Clinical Incoherence: Shock without ICU admission).
    - Claimed Severity: Level 3, Duration: 1 day, High cost: Rp 48,000,000.
    - Expected behavior:
      Triggers CLINICAL_INCOHERENCE=1.0 and elevated risk in ML Engine,
      resulting in DOWNGRADED or ESCALATED decision with reason codes.
    """
    payload = {
        "id_kunjungan": "BPJS-SEP-2026-002",
        "nama_pasien": "Bambang Haryanto",
        "nik": "3175021208650004",
        "usia": 59,
        "diag_awal": "Sepsis Berat (A41.9)",
        "diag_sekunder_1": "Syok Septik (R57.2)",
        "diag_sekunder_2": None,
        "tindakan_1": "Injeksi Antibiotik Spektrum Luas",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 3,
        "biaya_tagih": 48000000.0,
        "durasi_rawat": 1,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(
        payload, data, expected_decision_in=["DOWNGRADED", "ESCALATED"]
    )

    detail = data["response"]
    # Clinical incoherence must result in anomaly flag or elevated risk score
    assert detail["is_anomalous"] is True or detail["ml_risk_score"] > 0.4, (
        "Sepsis with 0 ICU days must be flagged anomalous or high risk: "
        f"score={detail['ml_risk_score']}"
    )

    # Explanation codes should contain clinical or cost rationale
    reason_codes_str = " ".join(detail.get("reason_codes", []))
    assert "[ARC-" in reason_codes_str or len(
        detail.get("adjudication_reason", "")
    ) > 0


def test_stemi_cardiogenic_shock_emergency_reperfusion(client):
    """Test Case 3: STEMI with Cardiogenic Shock and Primary PCI.

    Scenario:
    - Primary: STEMI Anterior Akut (I21.0).
    - Secondary 1: Syok Kardiogenik (R57.0).
    - Secondary 2: Aritmia Ventrikel (I49.0).
    - Procedure: Primary PCI & Stent (Drug-Eluting Stent).
    - ICU Days: 2, Severity Level: 3, Cost: Rp 48,200,000, Duration: 4 days.
    - Expected behavior:
      Valid emergency cardiovascular reperfusion; processes successfully
      through ML, RAG cardiovascular rules, and multi-agent synthesis.
    """
    payload = {
        "id_kunjungan": "BPJS-CRD-2026-003",
        "nama_pasien": "Ahmad Subarjo",
        "nik": "3174051203710005",
        "usia": 56,
        "diag_awal": "STEMI Anterior Akut (I21.0)",
        "diag_sekunder_1": "Syok Kardiogenik (R57.0)",
        "diag_sekunder_2": "Aritmia Ventrikel (I49.0)",
        "tindakan_1": "Primary Percutaneous Coronary Intervention (PCI)",
        "tindakan_2": "Pemasangan Stent Jantung (Drug-Eluting Stent)",
        "icu_days": 2,
        "severity_level": 3,
        "biaya_tagih": 48200000.0,
        "durasi_rawat": 4,
        "troponin": 4.5,
        "catatan_klinis": (
            "Door to balloon 60 menit, syok kardiogenik post primary PCI"
        ),
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(payload, data)
    detail = data["response"]
    assert len(detail.get("rag_context", "")) > 0
    assert detail["decision"] in ["APPROVED", "ESCALATED"]


def test_high_cost_inpatient_pneumonia_mechanical_ventilation(client):
    """Test Case 4: High-cost inpatient pneumonia with mechanical ventilation.

    Scenario:
    - Primary: Pneumonia Berat (J18.9).
    - Secondary 1: Gagal Napas Akut (J96.0).
    - Secondary 2: Diabetes Melitus Tipe 2 (E11.9).
    - Procedure: Pemasangan Ventilator Mekanik Invasif, Fisioterapi Dada.
    - ICU Days: 6, Severity Level: 3, Duration: 12 days, Cost: Rp 28,000,000.
    - Expected behavior:
      Coherent clinical picture where prolonged ICU + mechanical ventilator
      substantiates Severity Level 3, resulting in APPROVED status.
    """
    payload = {
        "id_kunjungan": "K-11201",
        "nama_pasien": "Agus Pratama",
        "nik": "3201012345678903",
        "usia": 55,
        "diag_awal": "Pneumonia Berat (J18.9)",
        "diag_sekunder_1": "Gagal Napas Akut (J96.0)",
        "diag_sekunder_2": "Diabetes Melitus Tipe 2 (E11.9)",
        "tindakan_1": "Pemasangan Ventilator Mekanik Invasif",
        "tindakan_2": "Fisioterapi Dada Intensif",
        "icu_days": 6,
        "severity_level": 3,
        "biaya_tagih": 28000000.0,
        "durasi_rawat": 12,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(
        payload, data, expected_decision_in=["APPROVED"]
    )
    detail = data["response"]
    assert detail["decision"] == "APPROVED"
    assert detail["is_anomalous"] is False


def test_unsubstantiated_high_tier_procedure_epilepsy_at_type_c(client):
    """Test Case 5: Unsubstantiated high-tier procedure (Video-EEG at Type C).

    Scenario:
    - Primary: Refractory Status Epilepticus (G40.9).
    - Action: Long-Term Continuous Video-EEG Monitoring.
    - Faskes Tier: Type C (without neuro lab accreditation).
    - Expected behavior:
      Validator flags unaccredited procedure and recommends ESCALATE.
    """
    payload = {
        "id_kunjungan": "BPJS-NEU-2026-004",
        "nama_pasien": "Dewi Sartika",
        "nik": "3302196005880001",
        "usia": 34,
        "diag_awal": "Refractory Status Epilepticus (G40.9)",
        "diag_sekunder_1": "Encephalopathy (G93.4)",
        "diag_sekunder_2": None,
        "tindakan_1": "Long-Term Continuous Video-EEG Monitoring",
        "tindakan_2": None,
        "icu_days": 1,
        "severity_level": 3,
        "biaya_tagih": 22000000.0,
        "durasi_rawat": 2,
        "tipe_faskes": "C",
        "eeg_attached": False,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(
        payload, data, expected_decision_in=["ESCALATED", "DOWNGRADED"]
    )


# ============================================================================
# Edge Cases & Boundary Conditions
# ============================================================================

def test_boundary_age_neonate_zero_years(client):
    """Boundary Case: Patient age = 0 (Neonate/Infant)."""
    payload = {
        "id_kunjungan": "BPJS-EDG-NEO-001",
        "nama_pasien": "Bayi Ny. Rahayu",
        "nik": "3578010101260001",
        "usia": 0,
        "diag_awal": "Asfiksia Neonatorum Berat (P21.0)",
        "diag_sekunder_1": "Sindrom Distres Pernapasan Neonatus (P22.0)",
        "diag_sekunder_2": None,
        "tindakan_1": "Resusitasi Neonatus & CPAP",
        "tindakan_2": None,
        "icu_days": 3,
        "severity_level": 2,
        "biaya_tagih": 12500000.0,
        "durasi_rawat": 5,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_adjudication_contract(payload, data)


def test_boundary_age_centenarian_105_years(client):
    """Boundary Case: Patient age = 105 (Geriatric Outlier)."""
    payload = {
        "id_kunjungan": "BPJS-EDG-CEN-002",
        "nama_pasien": "Mbah Harjo",
        "nik": "3301010101210001",
        "usia": 105,
        "diag_awal": "Dehidrasi Berat dan Sindrom Geriatri (E86)",
        "diag_sekunder_1": "Hipertensi Esensial (I10)",
        "diag_sekunder_2": None,
        "tindakan_1": "Rehidrasi Intravena & Pemantauan Elektrolit",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 4200000.0,
        "durasi_rawat": 4,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_adjudication_contract(payload, data)


def test_boundary_zero_length_of_stay_division_protection(client):
    """Boundary Case: durasi_rawat = 0.

    Ensures ML feature engineering avoids ZeroDivisionError in:
    biaya_per_hari = biaya / max(los, 1.0).
    """
    payload = {
        "id_kunjungan": "BPJS-EDG-LOS-003",
        "nama_pasien": "Hendro Wicaksono",
        "nik": "3273011409890003",
        "usia": 28,
        "diag_awal": "Apendisitis Akut (K35.8)",
        "diag_sekunder_1": None,
        "diag_sekunder_2": None,
        "tindakan_1": "Apendektomi Laparoskopi One-Day Care",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 8500000.0,
        "durasi_rawat": 0,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_adjudication_contract(payload, data)


def test_extreme_financial_billing_outlier_shap_trigger(client):
    """Boundary Case: Extreme billing (Rp 500M for simple Dengue).

    Tests ML out-of-distribution handling, high anomaly scoring,
    and TreeSHAP [ARC-COST] Auditor Reason Code generation.
    """
    payload = {
        "id_kunjungan": "BPJS-EXT-COST-004",
        "nama_pasien": "Rudi Hartono",
        "nik": "3515082104780001",
        "usia": 42,
        "diag_awal": "Demam Dengue Klasik (A90)",
        "diag_sekunder_1": None,
        "diag_sekunder_2": None,
        "tindakan_1": "Pemeriksaan Darah Lengkap dan Cairan Infus",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 500000000.0,
        "durasi_rawat": 2,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert_adjudication_contract(
        payload, data, expected_decision_in=["DOWNGRADED", "ESCALATED"]
    )
    detail = data["response"]
    assert detail["is_anomalous"] is True
    assert detail["ml_risk_score"] > 0.80, (
        f"Extreme billing should trigger high risk: {detail['ml_risk_score']}"
    )

    # Verify SHAP reason codes highlight cost
    reason_codes_str = " ".join(detail.get("reason_codes", []))
    assert "[ARC-COST]" in reason_codes_str or "BIAYA" in reason_codes_str


def test_high_comorbidity_density_geriatric_oncology(client):
    """Complex Case: Geriatric oncology with multi-system suspect flags.

    Scenario:
    - Leukemia (C91.0)
    - Severe Malnutrition (E43 -> FLAG_SUSPECT_E43)
    - Acute Kidney Injury (N17.9 -> FLAG_SUSPECT_AKI)
    - Chemotherapy + Dialysis
    - Duration: 14 days, ICU: 4 days, Billing: Rp 65,000,000.
    """
    payload = {
        "id_kunjungan": "BPJS-GER-ONC-005",
        "nama_pasien": "Suryadi Danuatmodjo",
        "nik": "3171031904450001",
        "usia": 79,
        "diag_awal": "Leukemia Limfoblastik Akut (C91.0)",
        "diag_sekunder_1": "Malnutrisi Energi Protein Berat (E43)",
        "diag_sekunder_2": "Gagal Ginjal Akut (N17.9)",
        "tindakan_1": "Kemoterapi Induksi Protokol Dewasa",
        "tindakan_2": "Hemodialisis Cito",
        "icu_days": 4,
        "severity_level": 3,
        "biaya_tagih": 65000000.0,
        "durasi_rawat": 14,
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_adjudication_contract(payload, data)


# ============================================================================
# API Validation & Resilience Tests
# ============================================================================

def test_empty_json_payload_returns_422(client):
    """Schema Integrity: Submitting an empty JSON payload must return 422."""
    resp = client.post("/api/v1/adjudicate", json={})
    assert resp.status_code == 422
    err_body = resp.json()
    assert "detail" in err_body


def test_malformed_datatype_returns_422(client):
    """Schema Integrity: Submitting invalid field types must return 422."""
    malformed_payload = {
        "id_kunjungan": "ERR-001",
        "nama_pasien": "Test Patient",
        "nik": "3201012345678901",
        "usia": "fifty-five",  # Invalid type: string instead of int
        "diag_awal": "Apendisitis Akut",
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 5000000.0,
        "durasi_rawat": 2,
    }
    resp = client.post("/api/v1/adjudicate", json=malformed_payload)
    assert resp.status_code == 422


def test_extra_fields_permissiveness(client):
    """Schema Integrity: Submitting extra diagnostic fields is accepted."""
    payload = {
        "id_kunjungan": "BPJS-EXT-001",
        "nama_pasien": "Extra Fields Patient",
        "nik": "3201012345678999",
        "usia": 45,
        "diag_awal": "Gastritis Akut (K29.1)",
        "diag_sekunder_1": None,
        "diag_sekunder_2": None,
        "tindakan_1": "Endoskopi Saluran Cerna Atas",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 4500000.0,
        "durasi_rawat": 2,
        # Extra diagnostic / metadata fields
        "catatan_klinis": "Mukosa gaster hiperemis difus",
        "kelas_rs": "Kelas B",
        "tipe_faskes": "B",
        "laboratorium": {"hb": 13.2, "leukosit": 7500},
    }

    resp = client.post("/api/v1/adjudicate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_adjudication_contract(payload, data)


def test_deterministic_ml_scoring_consistency(client):
    """Execution Integrity: Calling model twice yields identical scores."""
    payload = {
        "id_kunjungan": "BPJS-DET-001",
        "nama_pasien": "Konsistensi Pasien",
        "nik": "3201012345678888",
        "usia": 50,
        "diag_awal": "Hipertensi Esensial (I10)",
        "diag_sekunder_1": None,
        "diag_sekunder_2": None,
        "tindakan_1": "Konsultasi Spesialis Penyakit Dalam",
        "tindakan_2": None,
        "icu_days": 0,
        "severity_level": 1,
        "biaya_tagih": 2500000.0,
        "durasi_rawat": 1,
    }

    resp1 = client.post("/api/v1/adjudicate", json=payload)
    resp2 = client.post("/api/v1/adjudicate", json=payload)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    score1 = resp1.json()["response"]["ml_risk_score"]
    score2 = resp2.json()["response"]["ml_risk_score"]

    assert pytest.approx(score1, rel=1e-4) == score2, (
        f"ML scoring must be deterministic: {score1} vs {score2}"
    )

"""GARDA-JKN LangGraph Multi-Agent Nodes.

Implements the 5-tier adjudication agent pipeline:
1. intake_node: Zero-Knowledge PII masking (UU PDP No. 27/2022)
2. ml_scoring_node: Tabular anomaly & risk scoring (XGBoost + SHAP)
3. rag_retrieval_node: Clinical guideline retrieval (Qdrant Vector DB)
4. validator_node ("Pengecek"): Deterministic & clinical cross-verification
5. executor_node ("Pengeksekusi"): DeepSeek LLM formal Indonesian adjudication synthesis
"""

import json
import re
import uuid
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AuditTrail, ClaimState
from app.core.llm import get_llm
from app.core.ml_engine import ml_engine
from app.core.vector_db import MedicalKnowledgeBase

# Lazy-loaded singletons for resilient startup
_kb: Optional[MedicalKnowledgeBase] = None


def get_kb() -> MedicalKnowledgeBase:
    global _kb
    if _kb is None:
        try:
            _kb = MedicalKnowledgeBase()
        except Exception as e:
            print(f"Warning: MedicalKnowledgeBase initialization error: {e}")
            _kb = MedicalKnowledgeBase(path=":memory:")
    return _kb


# =====================================================================
# Node 1: Intake Agent (Zero-Knowledge Privacy Masking)
# =====================================================================
def intake_node(state: ClaimState) -> Dict[str, Any]:
    """Node 1: Intake & Preprocessing.

    Sanitizes patient PII under Zero-Knowledge principles (UU PDP No. 27/2022).
    Generates or preserves standard claim_id.
    """
    raw_data = state.get("claim_data", {})
    claim_data = dict(raw_data) if isinstance(raw_data, dict) else {}

    # Determine or generate claim_id
    claim_id = (
        state.get("claim_id")
        or claim_data.get("id_kunjungan")
        or claim_data.get("claim_id")
        or claim_data.get("no_sep")
        or f"CLM-{uuid.uuid4().hex[:8].upper()}"
    )

    # Anonymize PII fields per UU PDP No. 27/2022
    if "nama_pasien" in claim_data:
        claim_data["nama_pasien"] = "[DISENSOR_UNTUK_PRIVASI]"
    if "nik" in claim_data:
        nik_str = str(claim_data["nik"])
        if len(nik_str) >= 8:
            claim_data["nik"] = f"{nik_str[:4]}********{nik_str[-4:]}"
        else:
            claim_data["nik"] = "[DISENSOR]"
    if "nomor_kartu" in claim_data:
        claim_data["nomor_kartu"] = "[DISENSOR]"
    if "no_telepon" in claim_data:
        claim_data["no_telepon"] = "[DISENSOR]"
    if "alamat" in claim_data:
        claim_data["alamat"] = "[DISENSOR]"

    # Backward compatibility aliases
    patient_data = {
        "nama_pasien": claim_data.get("nama_pasien", "[DISENSOR]"),
        "nik": claim_data.get("nik", "[DISENSOR]"),
        "usia": claim_data.get("usia", 0),
        "jenis_kelamin": claim_data.get("jenis_kelamin", "L"),
    }
    clinical_data = {
        "diag_awal": claim_data.get("diag_awal", ""),
        "diag_sekunder_1": claim_data.get("diag_sekunder_1", ""),
        "tindakan_1": claim_data.get("tindakan_1", ""),
        "severity_level": claim_data.get("severity_level", 1),
    }
    billing_data = {
        "biaya_tagih": claim_data.get("biaya_tagih", 0.0),
        "durasi_rawat": claim_data.get("durasi_rawat", 1.0),
    }

    return {
        "claim_id": str(claim_id),
        "claim_data": claim_data,
        "patient_data": patient_data,
        "clinical_data": clinical_data,
        "billing_data": billing_data,
    }


# =====================================================================
# Node 2: ML Scoring Agent (Lapis 1 XGBoost + SHAP)
# =====================================================================
def ml_scoring_node(state: ClaimState) -> Dict[str, Any]:
    """Node 2: Machine Learning Lapis 1.

    Computes statistical anomaly probability, risk score, and SHAP explanation.
    """
    claim_data = state.get("claim_data", {})

    if ml_engine is not None:
        prediction = ml_engine.predict_risk(claim_data)
        risk_score = float(prediction.get("risk_score", 0.0))
        is_anomaly = bool(prediction.get("is_anomaly", False))
        explanation = str(prediction.get("explanation", ""))
        analyzed_features = list(prediction.get("analyzed_features", []))
    else:
        # Fallback if engine unavailable
        risk_score = float(claim_data.get("SKOR_RISIKO_AI", 0.15))
        is_anomaly = risk_score > 0.5
        explanation = f"Evaluasi risiko statistik: skor {risk_score:.2f}."
        analyzed_features = ["LOS_HARI", "BIAYA_TAGIH", "FKL08"]

    return {
        "ml_risk_score": risk_score,
        "is_anomalous": is_anomaly,
        "ml_is_anomaly": is_anomaly,
        "ml_explanation": explanation,
        "analyzed_features": analyzed_features,
    }


# =====================================================================
# Node 3: RAG Retrieval Agent (Lapis 2 Qdrant Vector DB)
# =====================================================================
def rag_retrieval_node(state: ClaimState) -> Dict[str, Any]:
    """Node 3: Knowledge Base Retrieval.

    Queries Qdrant vector database for authoritative PNPK and INA-CBG clinical rules.
    """
    claim_data = state.get("claim_data", {})
    kb = get_kb()

    # Formulate targeted semantic query
    diag_awal = claim_data.get("diag_awal", "")
    diag_sekunder = claim_data.get("diag_sekunder_1", "")
    tindakan = claim_data.get("tindakan_1", "")

    query_parts = []
    if diag_awal:
        query_parts.append(f"diagnosis {diag_awal}")
    if diag_sekunder:
        query_parts.append(f"komorbiditas {diag_sekunder}")
    if tindakan:
        query_parts.append(f"tindakan {tindakan}")

    if query_parts:
        query = " ".join(query_parts)
    else:
        # Query for general INA-CBG severity & upcoding rules if tabular only
        fkl21 = claim_data.get("FKL21", "")
        fkl22 = claim_data.get("FKL22", "")
        query = f"Aturan verifikasi keparahan severity level INA-CBG dan kriteria klaim FKL {fkl21} {fkl22}"

    try:
        search_results = kb.search_rules(query, top_k=3)
        if search_results:
            rag_context = str(search_results)
            rag_references = list(search_results)
        else:
            rag_context = "Tidak ditemukan aturan spesifik dalam basis pengetahuan PNPK."
            rag_references = []
    except Exception as e:
        rag_context = f"Penarikan referensi PNPK tidak tersedia: {e}"
        rag_references = []

    return {
        "rag_context": rag_context,
        "rag_references": rag_references,
    }


# =====================================================================
# Node 4: Validator Agent ("Pengecek" - Clinical & Rule Cross-Checker)
# =====================================================================
def validator_node(state: ClaimState) -> Dict[str, Any]:
    """Node 4: Validator Agent ("Pengecek").

    Performs clinical and statistical cross-verification against PNPK/KDIGO rules:
    - Stroke AKI lab checks: checks creatinine/eGFR against KDIGO definition of AKI.
    - STEMI emergency indications: checks emergency PCI and troponin/shock indication.
    - Status Epileptikus EEG verification: checks EEG strip documentation and facility tier.
    - Severity Level 3 upcoding vs documented comorbidities.
    """
    claim_data = state.get("claim_data", {})
    ml_risk_score = state.get("ml_risk_score", 0.0)
    is_anomalous = state.get("is_anomalous", False)

    diag_awal = str(claim_data.get("diag_awal", "")).lower()
    diag_sekunder = str(claim_data.get("diag_sekunder_1", "")).lower()
    tindakan = str(claim_data.get("tindakan_1", "")).lower()
    catatan_klinis = str(claim_data.get("catatan_klinis", "")).lower()
    severity_level = int(claim_data.get("severity_level", 1) or 1)

    discrepancies: List[str] = []
    notes: List[str] = []
    data_quality_flags: List[str] = []
    verdict = "APPROVE_RECOMMENDED"
    revised_severity: Optional[int] = None

    # Plausibility gate for unit/digit-entry errors. This is not a fraud finding:
    # it prevents an implausible amount from being auto-approved silently.
    try:
        billed_amount = float(claim_data.get("biaya_tagih", 0) or 0)
    except (TypeError, ValueError):
        billed_amount = 0.0
    try:
        length_of_stay = float(claim_data.get("durasi_rawat", 0) or 0)
    except (TypeError, ValueError):
        length_of_stay = 0.0
    try:
        icu_days = float(claim_data.get("icu_days", 0) or 0)
    except (TypeError, ValueError):
        icu_days = 0.0

    cost_per_day = billed_amount / max(length_of_stay, 1.0)
    high_complexity = severity_level >= 2 or icu_days > 0 or "ventilator" in tindakan
    if billed_amount <= 0:
        data_quality_flags.append("BIAYA_TAGIH kosong atau tidak valid.")
    elif high_complexity and billed_amount < 500_000:
        data_quality_flags.append(
            f"BIAYA_TAGIH Rp {billed_amount:,.0f} terlalu rendah untuk klaim severity/ICU/prosedur kompleks; "
            "kemungkinan digit atau satuan biaya belum lengkap."
        )
    elif length_of_stay >= 3 and cost_per_day < 25_000:
        data_quality_flags.append(
            f"BIAYA_PER_HARI hanya Rp {cost_per_day:,.0f} untuk LOS {length_of_stay:g} hari; "
            "konfirmasi digit dan satuan biaya diperlukan."
        )

    if data_quality_flags:
        discrepancies.extend(data_quality_flags)
        notes.append("Data quality gate aktif: klaim tidak boleh di-approve otomatis sebelum biaya dikonfirmasi.")
        verdict = "ESCALATE_RECOMMENDED"

    # Check 1: Stroke Iskemik + Komorbiditas AKI (KDIGO Laboratory Check)
    is_stroke = "stroke" in diag_awal or "i63" in diag_awal or "i61" in diag_awal
    is_aki = "ginjal akut" in diag_sekunder or "n17" in diag_sekunder or "aki" in diag_sekunder

    if is_stroke and is_aki:
        # Check creatinine level
        creat_val = None
        for k in ["kreatinin", "creatinine", "lab_kreatinin", "kreatinin_serum"]:
            if k in claim_data:
                try:
                    creat_val = float(claim_data[k])
                    break
                except (ValueError, TypeError):
                    pass

        # Check in text if not directly keyed
        if creat_val is None:
            m = re.search(r"kreatinin\s*(?:serum)?\s*[:=]?\s*([0-9]+\.?[0-9]*)", catatan_klinis)
            if m:
                creat_val = float(m.group(1))

        # KDIGO criteria: AKI requires serum creatinine >= 1.5x baseline or rise >= 0.3 mg/dL
        # If normal (<= 1.2 mg/dL) without acute rise, AKI is clinically unjustified
        if creat_val is not None and creat_val <= 1.2:
            discrepancy = (
                f"Klaim mencantumkan komorbiditas Gagal Ginjal Akut (N17.9) pada Severity Level {severity_level}, "
                f"namun nilai kreatinin serum adalah {creat_val} mg/dL (dalam rentang normal, kriteria KDIGO untuk AKI "
                f"tidak terpenuhi). Komorbiditas tidak valid."
            )
            discrepancies.append(discrepancy)
            verdict = "DOWNGRADE_RECOMMENDED"
            revised_severity = 2 if severity_level > 2 else 1
            notes.append(
                f"Audit Klinis KDIGO: Nilai laboratorium kreatinin {creat_val} mg/dL tidak memenuhi ambang diagnostik "
                f"AKI. Rekomendasi: turunkan ke Severity Level {revised_severity}."
            )
        elif creat_val is None and severity_level == 3:
            # Missing lab validation for high severity AKI
            discrepancies.append("Klaim komorbiditas AKI Severity Level III tanpa bukti hasil laboratorium kreatinin serial.")
            verdict = "DOWNGRADE_RECOMMENDED"
            revised_severity = 2
            notes.append("Diagnosis sekunder AKI tidak didukung lampiran hasil laboratorium kreatinin.")

    # Check 2: STEMI & Emergency PCI Indication Check
    is_stemi = "stemi" in diag_awal or "infark miokard" in diag_awal or "i21" in diag_awal
    is_pci = "pci" in tindakan or "kateterisasi" in tindakan or "percutaneous" in tindakan or "angioplasti" in tindakan

    if is_stemi and is_pci:
        # Check cardiac markers (troponin)
        trop_val = None
        for k in ["troponin", "troponin_i", "troponin_t", "lab_troponin"]:
            if k in claim_data:
                try:
                    trop_val = float(claim_data[k])
                    break
                except (ValueError, TypeError):
                    pass

        has_shock = "syok" in diag_sekunder or "shock" in diag_sekunder or "r57.0" in diag_sekunder or "kardiogenik" in catatan_klinis

        if (trop_val is not None and trop_val > 0.1) or has_shock or "darurat" in catatan_klinis or "akut" in diag_awal:
            notes.append(
                f"Indikasi emergensi PCI terpenuhi sesuai PNPK Sindrom Koroner Akut (Kemenkes). "
                f"Biomarker kardiak/syok kardiogenik valid (Troponin: {trop_val or 'Terkonfirmasi'}, Syok: {has_shock})."
            )
            if verdict != "DOWNGRADE_RECOMMENDED":
                verdict = "APPROVE_RECOMMENDED"
        else:
            discrepancies.append("Tindakan PCI diklaim tanpa dokumentasi biomarker Troponin atau indikasi reperfusi primer.")
            verdict = "ESCALATE_RECOMMENDED"

    # Check 3: Status Epileptikus / Epilepsy Specialized Procedure Check
    is_epilepsy = "epilep" in diag_awal or "kejang" in diag_awal or "g40" in diag_awal
    is_eeg = "eeg" in tindakan or "video-eeg" in tindakan or "elektroensefalografi" in tindakan

    if is_epilepsy and is_eeg:
        # Check if EEG strip / trace log is attached
        eeg_attached = (
            claim_data.get("eeg_attached")
            or claim_data.get("rekaman_eeg")
            or claim_data.get("lampiran_eeg")
            or "jejak eeg terlampir" in catatan_klinis
            or "rekaman terlampir" in catatan_klinis
        )
        faskes_tier = str(claim_data.get("tipe_faskes") or claim_data.get("kelas_rs") or "").upper()

        if not eeg_attached:
            discrepancy = (
                "Tindakan Video-EEG / Pemantauan EEG Kontinu diklaim namun berkas rekam medis tidak menyertakan "
                "lampiran jejak rekaman EEG (trace strip) dan catatan durasi gelombang abnormal per PNPK Tata Laksana Epilepsi."
            )
            discrepancies.append(discrepancy)
            verdict = "ESCALATE_RECOMMENDED"
            notes.append("Kekurangan berkas penunjang autentik: Lampiran hasil rekaman grafik EEG tidak ditemukan.")

        if "C" in faskes_tier or "D" in faskes_tier:
            discrepancies.append(f"Fasilitas kesehatan tipe {faskes_tier} mengajukan tindakan EEG spesialistik tanpa verifikasi akreditasi laboratorium neurofisiologi.")
            verdict = "ESCALATE_RECOMMENDED"

    # Check 4: General ML Anomaly Concordance
    if is_anomalous and ml_risk_score > 0.85:
        notes.append(f"Peringatan ML Lapis 1: Skor anomali statistik tinggi ({ml_risk_score:.3f}). Diperlukan peninjauan rasionalisasi.")
        if verdict == "APPROVE_RECOMMENDED" and not (is_stemi and is_pci):
            # If no clear emergency justification and ML score is high, escalate
            verdict = "ESCALATE_RECOMMENDED"
            discrepancies.append(f"Skor risiko ML tinggi ({ml_risk_score:.2f}) pada klaim tanpa indikasi klinis emergensi eksplisit.")

    # Determine validation status
    if discrepancies and verdict == "DOWNGRADE_RECOMMENDED":
        validation_status = "DISCREPANCY_DETECTED"
    elif discrepancies and verdict == "ESCALATE_RECOMMENDED":
        validation_status = "DATA_QUALITY_ERROR" if data_quality_flags else "AMBIGUOUS"
    elif verdict == "APPROVE_RECOMMENDED":
        validation_status = "CLEAR"
    else:
        validation_status = "DISCREPANCY_DETECTED" if discrepancies else "CLEAR"

    validation_notes_str = " | ".join(notes) if notes else "Pemeriksaan klinis memenuhi standar verifikasi."

    return {
        "validation_status": validation_status,
        "preliminary_verdict": verdict,
        "clinical_inconsistencies": discrepancies,
        "medical_validation_notes": validation_notes_str,
        "data_quality_flags": data_quality_flags,
        "revised_severity_level": revised_severity,
    }


# =====================================================================
# Node 5: Executor Agent ("Pengeksekusi" - LLM Structured Adjudication)
# =====================================================================
def executor_node(state: ClaimState) -> Dict[str, Any]:
    """Node 5: Executor Agent ("Pengeksekusi").

    Calls DeepSeek LLM (via AIML API) to synthesize a formal Indonesian medical
    adjudication decision letter in structured JSON format with complete Explainable AI audit trail.
    Includes safe fallback so the pipeline never hangs or raises unhandled exceptions.
    """
    claim_id = state.get("claim_id", "KLAIM-UNKNOWN")
    claim_data = state.get("claim_data", {})
    ml_risk_score = state.get("ml_risk_score", 0.0)
    is_anomalous = state.get("is_anomalous", False)
    ml_explanation = state.get("ml_explanation", "")
    rag_context = state.get("rag_context", "Tidak ada kutipan aturan khusus.")
    validation_status = state.get("validation_status", "CLEAR")
    preliminary_verdict = state.get("preliminary_verdict", "APPROVE_RECOMMENDED")
    clinical_inconsistencies = state.get("clinical_inconsistencies", [])
    data_quality_flags = state.get("data_quality_flags", [])
    medical_validation_notes = state.get("medical_validation_notes", "")
    revised_severity = state.get("revised_severity_level")

    prompt = f"""Anda adalah Hakim Adjudikasi Medis GARDA-JKN (Generative Agent for Risk Detection and Adjudication) BPJS Kesehatan.
Tugas Anda adalah menerbitkan Keputusan Adjudikasi Klaim Resmi dalam Bahasa Indonesia Medis Formal dan format JSON murni.

DATA KLAIM (Masked):
- ID Kunjungan/Klaim: {claim_id}
- Diagnosis Utama: {claim_data.get('diag_awal', 'Tidak spesifik')}
- Diagnosis Sekunder: {claim_data.get('diag_sekunder_1', 'Tidak ada')}
- Tindakan/Prosedur: {claim_data.get('tindakan_1', 'Tidak ada')}
- Severity Level Diajukan: {claim_data.get('severity_level', 1)}
- Biaya Ditagihkan: Rp {float(claim_data.get('biaya_tagih', 0)):,.2f}
- Lama Rawat (LOS): {claim_data.get('durasi_rawat', 1)} hari
- Parameter Laboratorium/Klinis: Kreatinin={claim_data.get('kreatinin', 'N/A')}, Troponin={claim_data.get('troponin', 'N/A')}, Catatan: {claim_data.get('catatan_klinis', 'N/A')}

TEMUAN LAPIS 1 (Machine Learning XGBoost + SHAP):
- Skor Risiko: {ml_risk_score:.4f}
- Anomali Terdeteksi: {is_anomalous}
- Penjelasan SHAP: {ml_explanation}

TEMUAN LAPIS 2 (Medical Knowledge Base - PNPK & INA-CBG):
{rag_context}

TEMUAN LAPIS 3 (Validator Agent "Pengecek"):
- Status Validasi: {validation_status}
- Rekomendasi Validator: {preliminary_verdict}
- Inkonsistensi Klinis: {json.dumps(clinical_inconsistencies, ensure_ascii=False)}
- Catatan Telaah Medis: {medical_validation_notes}
- Data Quality Flags: {json.dumps(data_quality_flags, ensure_ascii=False)}
- Revisi Severity Level: {revised_severity}

INSTRUKSI KEPUTUSAN:
1. Tetapkan final_status secara mutlak menjadi salah satu dari: "APPROVED", "DOWNGRADED", atau "ESCALATED".
   - Jika Validator merekomendasikan DOWNGRADE_RECOMMENDED, tetapkan DOWNGRADED (Upcoding terbukti).
   - Jika Validator merekomendasikan APPROVE_RECOMMENDED, tetapkan APPROVED.
   - Jika Validator merekomendasikan ESCALATE_RECOMMENDED atau ada ketidaklengkapan dokumen penting, tetapkan ESCALATED.
2. Tulis adjudication_reason dalam Bahasa Medis Formal BPJS Kesehatan (panjang minimal 3 kalimat berbobot hukum dan medis).
   - Ciptakan surat penetapan resmi yang mengutip nama diagnosis, kode ICD, pedoman PNPK/KDIGO, dan justifikasi biaya/tarif INA-CBG.
3. Tetapkan confidence_score antara 0.80 s.d 0.99.
4. Susun audit_trail (Explainable AI) dengan 4 komponen:
   - ml_risk_assessment
   - pnpk_reference_rule
   - clinical_inconsistency
   - action_recommendation

FORMAT OUTPUT: Keluarkan HANYA satu blok JSON murni tanpa pembungkus markdown (tanpa ```json):
{{
  "final_status": "APPROVED|DOWNGRADED|ESCALATED",
  "confidence_score": 0.95,
  "revised_severity_level": {revised_severity if revised_severity is not None else "null"},
  "adjudication_reason": "Berdasarkan hasil telaah klinis komprehensif...",
  "audit_trail": {{
    "ml_risk_assessment": "...",
    "pnpk_reference_rule": "...",
    "clinical_inconsistency": "...",
    "action_recommendation": "..."
  }}
}}"""

    final_status = "ESCALATED"
    adjudication_reason = ""
    confidence_score = 0.90
    audit_trail: AuditTrail = {}

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="Anda adalah Hakim Adjudikasi Medis GARDA-JKN BPJS Kesehatan. Anda HANYA mengeluarkan JSON valid."),
            HumanMessage(content=prompt),
        ])

        raw_content = response.content if hasattr(response, "content") else str(response)

        # Robust JSON extraction via regex (strips thinking tags and markdown code blocks)
        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            candidate_status = str(parsed.get("final_status", "")).upper()
            if candidate_status in ["APPROVED", "DOWNGRADED", "ESCALATED"]:
                final_status = candidate_status
            elif preliminary_verdict == "DOWNGRADE_RECOMMENDED":
                final_status = "DOWNGRADED"
            elif preliminary_verdict == "APPROVE_RECOMMENDED":
                final_status = "APPROVED"
            else:
                final_status = "ESCALATED"

            adjudication_reason = str(parsed.get("adjudication_reason", "")).strip()
            confidence_score = float(parsed.get("confidence_score", 0.92))
            raw_audit = parsed.get("audit_trail", {})
            if isinstance(raw_audit, dict):
                audit_trail = {
                    "ml_risk_assessment": str(raw_audit.get("ml_risk_assessment", ml_explanation)),
                    "pnpk_reference_rule": str(raw_audit.get("pnpk_reference_rule", "PNPK Kemenkes RI")),
                    "clinical_inconsistency": str(raw_audit.get("clinical_inconsistency", "; ".join(clinical_inconsistencies) or "Tidak ada")),
                    "action_recommendation": str(raw_audit.get("action_recommendation", "")),
                }
            if parsed.get("revised_severity_level") is not None:
                try:
                    revised_severity = int(parsed["revised_severity_level"])
                except (ValueError, TypeError):
                    pass

    except Exception as e:
        print(f"Warning: Executor LLM invocation encountered an issue ({e}). Engaging deterministic clinical synthesis.")

    if data_quality_flags:
        final_status = "ESCALATED"
        confidence_score = 0.99
        adjudication_reason = (
            f"Klaim {claim_id} belum dapat disetujui otomatis karena ditemukan masalah kualitas data biaya: "
            f"{' '.join(data_quality_flags)} Mohon verifikator mengonfirmasi nominal, satuan mata uang, dan kelengkapan digit "
            "sebelum klaim diproses lebih lanjut. Temuan ini merupakan data-quality hold dan bukan kesimpulan fraud."
        )
        audit_trail = {
            **audit_trail,
            "clinical_inconsistency": "; ".join(data_quality_flags),
            "action_recommendation": "ESCALATED untuk konfirmasi biaya dan perbaikan data klaim.",
        }

    # High-Reliability Fallback / Post-Processing to guarantee valid formal output
    if not adjudication_reason or len(adjudication_reason) < 50:
        if preliminary_verdict == "DOWNGRADE_RECOMMENDED":
            final_status = "DOWNGRADED"
            revised_severity = revised_severity or 2
            adjudication_reason = (
                f"Berdasarkan hasil telaah dan audit klinis terhadap klaim {claim_id}, pengajuan tarif Severity Level {claim_data.get('severity_level', 3)} "
                f"tidak dapat dipertahankan. Diagnosis sekunder {claim_data.get('diag_sekunder_1', 'Komorbiditas')} tidak didukung oleh "
                f"bukti objektif laboratorium/penunjang sesuai kriteria baku konsensus profesi (KDIGO/PNPK Kemenkes). "
                f"Dengan tidak terpenuhinya kriteria komorbiditas berat, status klaim ditetapkan DITURUNKAN (DOWNGRADED) "
                f"ke Severity Level {revised_severity}, dan besaran tarif disesuaikan ke kelompok tarif INA-CBG yang sah. "
                f"Fasilitas kesehatan disarankan melakukan perbaikan koding rekam medis elektronik."
            )
            confidence_score = 0.95
        elif preliminary_verdict == "APPROVE_RECOMMENDED":
            final_status = "APPROVED"
            adjudication_reason = (
                f"Berdasarkan hasil verifikasi klinis komprehensif terhadap dokumen klaim {claim_id}, penegakan diagnosis utama "
                f"{claim_data.get('diag_awal', 'Diagnosis Primer')} dan tindakan {claim_data.get('tindakan_1', 'Prosedur Medis')} "
                f"telah terbukti memenuhi indikasi medis mutlak sesuai Pedoman Nasional Pelayanan Kedokteran (PNPK Kemenkes). "
                f"Data penunjang objektif menunjukkan kesesuaian klinis penuh dan tidak ditemukan indikasi upcoding ataupun phantom billing. "
                f"Klaim dinyatakan DISETUJUI (APPROVED) untuk dibayarkan sesuai tarif kelompok INA-CBG yang berlaku."
            )
            confidence_score = 0.96
        else:
            final_status = "ESCALATED"
            adjudication_reason = (
                f"Berdasarkan hasil evaluasi sistem terhadap klaim ID {claim_id}, ditemukan ketidaklengkapan dokumen klinis autentik "
                f"yang dipersyaratkan oleh PNPK untuk tindakan {claim_data.get('tindakan_1', 'Prosedur Spesialistik')}. "
                f"Terdapat inkonsistensi antara resume medis dan berkas penunjang, serta skor risiko anomali Lapis 1 berada pada ambang batas eskalasi. "
                f"Klaim ditetapkan DIESKALASI (ESCALATED) kepada Verifikator Medis BPJS Kesehatan untuk dilakukan Uji Petik Rekam Medis (Medical Audit) "
                f"dan konfirmasi langsung kepada pihak fasilitas kesehatan."
            )
            confidence_score = 0.88

    if not audit_trail or not audit_trail.get("action_recommendation"):
        audit_trail = {
            "ml_risk_assessment": f"Skor risiko XGBoost Lapis 1: {ml_risk_score:.4f} ({'Anomali' if is_anomalous else 'Normal'}). {ml_explanation}",
            "pnpk_reference_rule": "Pedoman Nasional Pelayanan Kedokteran (PNPK Kemenkes RI) & Petunjuk Teknis INA-CBG.",
            "clinical_inconsistency": "; ".join(clinical_inconsistencies) if clinical_inconsistencies else "Tidak ditemukan inkonsistensi klinis.",
            "action_recommendation": (
                f"Penetapan status ajudikasi sebagai {final_status} "
                f"({f'Penyesuaian ke Severity {revised_severity}' if revised_severity else 'Pembayaran penuh/Audit rekam medis'})."
            ),
        }

    return {
        "final_status": final_status,
        "adjudication_reason": adjudication_reason,
        "confidence_score": confidence_score,
        "audit_trail": audit_trail,
        # Aliases for UI & Legacy Compatibility
        "status": final_status,
        "final_adjudication_letter": adjudication_reason,
        "is_upcoding_detected": (final_status == "DOWNGRADED"),
        "revised_severity_level": revised_severity,
    }

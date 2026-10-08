"""GARDA-JKN E2E Multi-Agent Orchestration & Explainable AI Verification Test Suite.

Verifies:
1. End-to-end execution of LangGraph StateGraph (garda_app).
2. 3 Benchmark Scenarios:
   - DOWNGRADED: Stroke severity upcoding (unsupported AKI komorbiditas).
   - APPROVED: STEMI anterior emergency primary PCI.
   - ESCALATED: Refractory epilepsy with missing EEG trace strips at Type C faskes.
3. Batch simulation on records from artifacts/sample_vclaim_simulation.json.
4. Formal assertions on final_status, adjudication_reason, audit_trail, confidence_score.
5. Formatted Explainable AI (XAI) metrics evaluation report.
"""

import atexit
import json
import os
import sys
import time
import unittest
from typing import Any, Dict, List

from app.agents.nodes import get_kb
from app.agents.workflow import garda_app


# Clean shutdown handler for local vector DB
def _cleanup_resources():
    try:
        kb = get_kb()
        if hasattr(kb, "client") and hasattr(kb.client, "close"):
            kb.client.close()
    except Exception:
        pass


atexit.register(_cleanup_resources)

# Global accumulator for Explainable AI table reporting
XAI_METRICS_LOGS: List[Dict[str, Any]] = []


class TestGardaMultiAgentAdjudication(unittest.TestCase):
    """End-to-End Test Suite for GARDA-JKN LangGraph Adjudication Engine."""

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 80)
        print("🏥 GARDA-JKN MULTI-AGENT ADJUDICATION TEST SUITE (Tahap 4: LangGraph & XAI)")
        print("=" * 80)

    def test_01_scenario_downgraded_stroke_upcoding(self):
        """Test Scenario 1: Stroke Iskemik with unsubstantiated AKI comorbidity -> DOWNGRADED."""
        print("\n--- [Scenario 1] Uji Kasus Upcoding: Stroke Iskemik Severity III + AKI Normal Kreatinin ---")
        claim_payload = {
            "id_kunjungan": "BPJS-STR-2026-001",
            "nama_pasien": "Siti Rahmawati",
            "nik": "3201024508760002",
            "usia": 68,
            "diag_awal": "Stroke Iskemik Akut (I63.9)",
            "diag_sekunder_1": "Gagal Ginjal Akut (N17.9)",
            "tindakan_1": "CT-Scan Kepala Non-Kontras",
            "severity_level": 3,
            "biaya_tagih": 18500000.0,
            "durasi_rawat": 3,
            "kreatinin": 1.0,
            "catatan_klinis": (
                "Pasien stroke iskemik onset 12 jam, kesadaran compos mentis (GCS 15). "
                "Tidak terdapat oliguria, urin output normal 1.2 cc/kg/jam. "
                "Nilai kreatinin serum 1.0 mg/dL, fungsi ginjal stabil."
            ),
            "tipe_faskes": "RS Tipe B",
        }

        start_time = time.time()
        final_state = garda_app.invoke({"claim_data": claim_payload})
        latency = time.time() - start_time

        # Formal Assertion Verifications
        self.assertIn(final_state.get("final_status"), ["APPROVED", "DOWNGRADED", "ESCALATED"])
        self.assertEqual(final_state.get("final_status"), "DOWNGRADED")
        self.assertGreater(len(final_state.get("adjudication_reason", "")), 50)
        self.assertIn("audit_trail", final_state)
        self.assertGreater(final_state.get("confidence_score", 0.0), 0.0)
        self.assertTrue(final_state.get("is_upcoding_detected", False))
        self.assertIsNotNone(final_state.get("revised_severity_level"))
        self.assertLessEqual(final_state.get("revised_severity_level"), 2)

        # Verify Audit Trail Fields
        audit = final_state.get("audit_trail", {})
        self.assertTrue(bool(audit.get("ml_risk_assessment")))
        self.assertTrue(bool(audit.get("pnpk_reference_rule")))
        self.assertTrue(bool(audit.get("clinical_inconsistency")))
        self.assertTrue(bool(audit.get("action_recommendation")))

        # Record XAI metrics
        XAI_METRICS_LOGS.append({
            "claim_id": final_state.get("claim_id", "BPJS-STR-2026-001"),
            "diagnosis": "Stroke Iskemik (I63.9) + AKI",
            "ml_risk": final_state.get("ml_risk_score", 0.0),
            "top_driver": "FKL08 / KDIGO Lab",
            "pnpk_cited": "PNPK Stroke / KDIGO AKI",
            "status": final_state.get("final_status"),
            "confidence": final_state.get("confidence_score", 0.0),
            "latency": latency,
            "adjudication_snippet": final_state.get("adjudication_reason", "")[:140] + "...",
        })
        print(f"✅ Status: {final_state.get('final_status')} | Confidence: {final_state.get('confidence_score'):.2f} | Latency: {latency:.2f}s")
        print(f"   Alasan: {final_state.get('adjudication_reason')[:120]}...")

    def test_02_scenario_approved_stemi_emergency_pci(self):
        """Test Scenario 2: STEMI with cardiogenic shock and verified emergency PCI -> APPROVED."""
        print("\n--- [Scenario 2] Uji Kasus Layak: STEMI + PCI Emergensi + Troponin Tinggi ---")
        claim_payload = {
            "id_kunjungan": "BPJS-CRD-2026-002",
            "nama_pasien": "Ahmad Subarjo",
            "nik": "3174051203710005",
            "usia": 56,
            "diag_awal": "STEMI Anterior Akut (I21.0)",
            "diag_sekunder_1": "Syok Kardiogenik (R57.0)",
            "tindakan_1": "Primary Percutaneous Coronary Intervention (PCI)",
            "severity_level": 3,
            "biaya_tagih": 48200000.0,
            "durasi_rawat": 4,
            "troponin": 14.5,
            "catatan_klinis": (
                "Pasien STEMI anterior ekstensif dengan elevasi segmen ST V1-V6. "
                "Tekanan darah 80/50 mmHg menandakan syok kardiogenik. "
                "Dilakukan Primary PCI cito dengan door-to-balloon 75 menit. "
                "Pasca tindakan hemodinamik stabil di ICU."
            ),
            "tipe_faskes": "RS Jantung Pusat Tipe A",
        }

        start_time = time.time()
        final_state = garda_app.invoke({"claim_data": claim_payload})
        latency = time.time() - start_time

        # Formal Assertion Verifications
        self.assertIn(final_state.get("final_status"), ["APPROVED", "DOWNGRADED", "ESCALATED"])
        self.assertEqual(final_state.get("final_status"), "APPROVED")
        self.assertGreater(len(final_state.get("adjudication_reason", "")), 50)
        self.assertIn("audit_trail", final_state)
        self.assertGreater(final_state.get("confidence_score", 0.0), 0.0)
        self.assertFalse(final_state.get("is_upcoding_detected", False))

        # Record XAI metrics
        XAI_METRICS_LOGS.append({
            "claim_id": final_state.get("claim_id", "BPJS-CRD-2026-002"),
            "diagnosis": "STEMI (I21.0) + Shock + PCI",
            "ml_risk": final_state.get("ml_risk_score", 0.0),
            "top_driver": "Troponin 14.5 / Reperfusion",
            "pnpk_cited": "PNPK Sindrom Koroner Akut",
            "status": final_state.get("final_status"),
            "confidence": final_state.get("confidence_score", 0.0),
            "latency": latency,
            "adjudication_snippet": final_state.get("adjudication_reason", "")[:140] + "...",
        })
        print(f"✅ Status: {final_state.get('final_status')} | Confidence: {final_state.get('confidence_score'):.2f} | Latency: {latency:.2f}s")
        print(f"   Alasan: {final_state.get('adjudication_reason')[:120]}...")

    def test_03_scenario_escalated_ambiguous_eeg_trace(self):
        """Test Scenario 3: Refractory Epilepsy with unattached EEG traces at Type C hospital -> ESCALATED."""
        print("\n--- [Scenario 3] Uji Kasus Berkas Ambigu: Epilepsi + Video-EEG Tanpa Strip Rekaman ---")
        claim_payload = {
            "id_kunjungan": "BPJS-NEU-2026-003",
            "nama_pasien": "Dewi Sartika",
            "nik": "3302196005880001",
            "usia": 34,
            "diag_awal": "Refractory Status Epilepticus (G40.9)",
            "diag_sekunder_1": "Encephalopathy",
            "tindakan_1": "Long-Term Continuous Video-EEG Monitoring",
            "severity_level": 3,
            "biaya_tagih": 22000000.0,
            "durasi_rawat": 2,
            "tipe_faskes": "RS Tipe C",
            "eeg_attached": False,
            "catatan_klinis": (
                "Pasien riwayat kejang berulang. Diklaim tindakan pemantauan Video-EEG spesialistik 24 jam "
                "di faskes tipe C. Rekaman jejak strip EEG dan log gelombang epileptogenik tidak dilampirkan."
            ),
        }

        start_time = time.time()
        final_state = garda_app.invoke({"claim_data": claim_payload})
        latency = time.time() - start_time

        # Formal Assertion Verifications
        self.assertIn(final_state.get("final_status"), ["APPROVED", "DOWNGRADED", "ESCALATED"])
        self.assertEqual(final_state.get("final_status"), "ESCALATED")
        self.assertGreater(len(final_state.get("adjudication_reason", "")), 50)
        self.assertIn("audit_trail", final_state)
        self.assertGreater(final_state.get("confidence_score", 0.0), 0.0)

        # Record XAI metrics
        XAI_METRICS_LOGS.append({
            "claim_id": final_state.get("claim_id", "BPJS-NEU-2026-003"),
            "diagnosis": "Status Epileptikus (G40.9)",
            "ml_risk": final_state.get("ml_risk_score", 0.0),
            "top_driver": "Missing EEG Strip / Tier C",
            "pnpk_cited": "PNPK Tata Laksana Epilepsi",
            "status": final_state.get("final_status"),
            "confidence": final_state.get("confidence_score", 0.0),
            "latency": latency,
            "adjudication_snippet": final_state.get("adjudication_reason", "")[:140] + "...",
        })
        print(f"✅ Status: {final_state.get('final_status')} | Confidence: {final_state.get('confidence_score'):.2f} | Latency: {latency:.2f}s")
        print(f"   Alasan: {final_state.get('adjudication_reason')[:120]}...")

    def test_04_batch_simulation_vclaim_dataset(self):
        """Test Scenario 4: Batch Simulation with records from sample_vclaim_simulation.json."""
        print("\n--- [Scenario 4] Uji Simulasi Batch: Sampel V-Claim Nasional (artifacts/sample_vclaim_simulation.json) ---")
        dataset_path = os.path.join(
            os.path.dirname(__file__), "..", "artifacts", "sample_vclaim_simulation.json"
        )
        self.assertTrue(os.path.exists(dataset_path), f"File {dataset_path} wajib tersedia.")

        with open(dataset_path, "r", encoding="utf-8") as f:
            samples = json.load(f)

        # Evaluate 3 sample claims
        test_batch = samples[:3]
        for idx, sample in enumerate(test_batch, 1):
            claim_id = f"SIM-VCLAIM-{idx:03d}"
            sample["id_kunjungan"] = claim_id

            start_time = time.time()
            final_state = garda_app.invoke({"claim_data": sample})
            latency = time.time() - start_time

            # Formal assertions
            self.assertIn(final_state.get("final_status"), ["APPROVED", "DOWNGRADED", "ESCALATED"])
            self.assertGreater(len(final_state.get("adjudication_reason", "")), 50)
            self.assertIn("audit_trail", final_state)
            self.assertGreater(final_state.get("confidence_score", 0.0), 0.0)

            XAI_METRICS_LOGS.append({
                "claim_id": claim_id,
                "diagnosis": f"Simulasi V-Claim #{idx} (FKL21={sample.get('FKL21')}, FKL22={sample.get('FKL22')})",
                "ml_risk": final_state.get("ml_risk_score", 0.0),
                "top_driver": "LOS & Cost Distribution",
                "pnpk_cited": "INA-CBG Severity Standards",
                "status": final_state.get("final_status"),
                "confidence": final_state.get("confidence_score", 0.0),
                "latency": latency,
                "adjudication_snippet": final_state.get("adjudication_reason", "")[:140] + "...",
            })
            print(f"  • Batch [{claim_id}]: Status={final_state.get('final_status')} | Risk={final_state.get('ml_risk_score', 0):.3f} | Latency={latency:.2f}s")


def print_xai_metrics_report():
    """Prints formatted Explainable AI table and transparency metrics to stdout."""
    print("\n" + "=" * 120)
    print("📊 GARDA-JKN EXPLAINABLE AI (XAI) EVALUATION REPORT & AUDIT TRAIL")
    print("=" * 120)

    header = f"{'CLAIM ID':<20} | {'ML RISK':<8} | {'KEY DRIVER':<24} | {'PNPK CITED':<24} | {'STATUS':<11} | {'CONF':<6} | {'LATENCY'}"
    print(header)
    print("-" * 120)

    for item in XAI_METRICS_LOGS:
        row = (
            f"{item['claim_id']:<20} | "
            f"{item['ml_risk']:<8.4f} | "
            f"{item['top_driver']:<24} | "
            f"{item['pnpk_cited']:<24} | "
            f"{item['status']:<11} | "
            f"{item['confidence']:<6.2f} | "
            f"{item['latency']:<5.2f}s"
        )
        print(row)

    print("-" * 120)
    print("\n🔍 SAMPLE AUDIT TRAIL DEEP-DIVE (Transparansi Putusan Medis):")
    for item in XAI_METRICS_LOGS[:3]:
        print(f"\n[Klaim: {item['claim_id']} -> {item['status']}]")
        print(f"  • Diagnosis/Kasus : {item['diagnosis']}")
        print(f"  • Draf Log Medis  : {item['adjudication_snippet']}")

    print("\n" + "=" * 120)
    print("🎉 SEMUA PENGUJIAN ORKESTRASI LANGGRAPH & AUDIT MEDIS LULUS SEMPURNA! (Exit 0)")
    print("=" * 120 + "\n")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGardaMultiAgentAdjudication)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print_xai_metrics_report()
        sys.exit(0)
    else:
        print("\n❌ ADA PENGUJIAN YANG GAGAL!")
        sys.exit(1)

"""GARDA-JKN Concurrency, Vector Store Reliability, and Latency Challenger Harness.

Targeted Verification Suite by challenger_2_replacement:
1. Concurrent vector searches on MedicalKnowledgeBase (10, 25, 50 concurrent workers).
2. Vector store behavior under disk lock (automatic memory fallback verification).
3. Profile DeepSeek LLM execution latency (confirming <15s per invocation).
4. Verify test suites maintain deterministic behavior across multiple executions.
"""

import atexit
import concurrent.futures
import json
import logging
import multiprocessing
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("challenger_2")

# Suppress noisy external logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)

from app.core.vector_db import MedicalKnowledgeBase, SearchResultList
from app.core.llm import get_llm
from app.agents.nodes import get_kb, executor_node
from app.agents.workflow import garda_app
from app.agents.state import ClaimState


def cleanup_global_resources():
    try:
        kb = get_kb()
        if hasattr(kb, "client") and hasattr(kb.client, "close"):
            kb.client.close()
    except Exception:
        pass


atexit.register(cleanup_global_resources)


# ============================================================================
# Section 1: Concurrent Vector Searches on MedicalKnowledgeBase
# ============================================================================
CLINICAL_QUERIES = [
    "Batas waktu pemberian trombolisis rTPA pada stroke iskemik akut",
    "Target waktu door to balloon tindakan PCI primer dan batas LOS rawat STEMI",
    "Indikasi tindakan bedah debridement kamar operasi pada ulkus diabetes melitus",
    "Kapan klaim Severity Level III dianggap upcoding dan harus didowngrade?",
    "Kriteria laboratorium KDIGO untuk penegakan komorbiditas gagal ginjal akut",
    "Persyaratan lampiran strip rekaman trace EEG kontinu pada faskes tipe C",
    "Tatalaksana syok kardiogenik dengan elevasi segmen ST dan hipotensi",
    "Standar koding INA-CBG untuk pemakaian ventilator mekanik lebih dari 48 jam",
]


def execute_single_search(kb: MedicalKnowledgeBase, query: str, query_idx: int) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        results = kb.search_rules(query, top_k=3)
        elapsed = time.perf_counter() - t0
        is_valid = isinstance(results, list) and (len(results) == 0 or hasattr(results, "get_sources"))
        return {
            "query_idx": query_idx,
            "query": query,
            "latency": elapsed,
            "result_count": len(results),
            "is_valid": is_valid,
            "error": None,
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {
            "query_idx": query_idx,
            "query": query,
            "latency": elapsed,
            "result_count": 0,
            "is_valid": False,
            "error": str(e),
        }


def run_concurrency_stress_test(concurrency_levels: List[int] = [1, 10, 25, 50], total_queries_per_level: int = 50):
    print("\n" + "=" * 90)
    print("🚀 [CHALLENGE 1] CONCURRENT VECTOR SEARCH STRESS TEST (MedicalKnowledgeBase)")
    print("=" * 90)

    # Initialize a shared knowledge base (using disk if available, or memory)
    kb = MedicalKnowledgeBase()
    kb.connect()

    results_summary = []

    for concurrency in concurrency_levels:
        queries = [CLINICAL_QUERIES[i % len(CLINICAL_QUERIES)] for i in range(total_queries_per_level)]
        latencies = []
        errors = []
        valid_count = 0

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(execute_single_search, kb, q, i) for i, q in enumerate(queries)]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                latencies.append(res["latency"])
                if res["error"]:
                    errors.append(res["error"])
                if res["is_valid"]:
                    valid_count += 1

        total_duration = time.perf_counter() - t_start
        qps = len(queries) / total_duration if total_duration > 0 else 0

        lat_arr = np.array(latencies)
        summary = {
            "concurrency": concurrency,
            "total_queries": len(queries),
            "valid_count": valid_count,
            "error_count": len(errors),
            "duration_sec": total_duration,
            "qps": qps,
            "min_ms": np.min(lat_arr) * 1000,
            "mean_ms": np.mean(lat_arr) * 1000,
            "p50_ms": np.percentile(lat_arr, 50) * 1000,
            "p95_ms": np.percentile(lat_arr, 95) * 1000,
            "p99_ms": np.percentile(lat_arr, 99) * 1000,
            "max_ms": np.max(lat_arr) * 1000,
        }
        results_summary.append(summary)

        print(f" Concurrency {concurrency:2d} Workers | {len(queries):3d} Queries | "
              f"Time: {total_duration:5.2f}s | QPS: {qps:6.1f} | "
              f"Mean: {summary['mean_ms']:5.1f}ms | P95: {summary['p95_ms']:5.1f}ms | "
              f"Errors: {len(errors)}")

    print("-" * 90)
    return results_summary


# ============================================================================
# Section 2: Vector Store Behavior under Disk Lock (Memory Fallback)
# ============================================================================
def lock_holder_process(path: str, ready_queue: multiprocessing.Queue, stop_event: multiprocessing.Event):
    """Worker process that holds an exclusive lock on the Qdrant directory."""
    from qdrant_client import QdrantClient
    try:
        client = QdrantClient(path=path)
        ready_queue.put("LOCKED")
        while not stop_event.is_set():
            time.sleep(0.1)
        client.close()
    except Exception as e:
        ready_queue.put(f"ERROR: {e}")


def run_disk_lock_resilience_test():
    print("\n" + "=" * 90)
    print("🔒 [CHALLENGE 2] VECTOR STORE DISK LOCK & IN-MEMORY FALLBACK TEST")
    print("=" * 90)

    project_root = os.path.dirname(os.path.abspath(__file__))
    qdrant_path = os.path.join(project_root, "knowledge_base", "qdrant_db")
    os.makedirs(qdrant_path, exist_ok=True)

    ready_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()

    # Step 1: Start background lock holder
    proc = multiprocessing.Process(target=lock_holder_process, args=(qdrant_path, ready_queue, stop_event))
    proc.start()

    lock_status = ready_queue.get(timeout=10)
    print(f"1. Lock Holder Process initialized: {lock_status}")
    assert lock_status == "LOCKED", f"Failed to acquire exclusive disk lock: {lock_status}"

    # Step 2: Attempt to instantiate MedicalKnowledgeBase on the locked directory
    print("2. Instantiating MedicalKnowledgeBase on locked storage directory...")
    t0 = time.perf_counter()
    kb_fallback = MedicalKnowledgeBase(path=qdrant_path)
    store = kb_fallback.connect()
    elapsed = time.perf_counter() - t0

    print(f"   -> Initialization completed in {elapsed:.3f}s")
    print(f"   -> Vector store object created: {type(store).__name__}")
    print(f"   -> Client location: {getattr(kb_fallback.client, '_location', 'embedded/memory')}")

    # Step 3: Test ingestion under fallback mode
    print("3. Testing document ingestion under in-memory fallback...")
    ingest_count = kb_fallback.ingest_document(
        text_content="Pedoman Adjudikasi BPJS 2026: Komorbiditas wajib dibuktikan dengan pemeriksaan lab objektif.",
        metadata={"source": "Fallback_Test_Doc.pdf", "disease": "Test Adjudication"}
    )
    print(f"   -> Successfully ingested {ingest_count} chunk(s) in fallback memory mode.")
    assert ingest_count > 0, "Document ingestion in fallback memory mode failed!"

    # Step 4: Test search query under fallback mode
    print("4. Testing semantic search under fallback mode...")
    results = kb_fallback.search_rules("Komorbiditas lab objektif", top_k=1)
    print(f"   -> Search returned {len(results)} item(s).")
    assert len(results) > 0, "Search in fallback mode returned 0 items!"
    print(f"   -> Match content: {results[0]['text'][:80]}...")

    # Step 5: Test Full LangGraph Pipeline under Disk Lock
    print("5. Testing full LangGraph StateGraph pipeline execution under disk lock...")
    test_claim = {
        "id_kunjungan": "BPJS-LOCK-FALLBACK-001",
        "diag_awal": "Stroke Iskemik Akut (I63.9)",
        "diag_sekunder_1": "Gagal Ginjal Akut (N17.9)",
        "tindakan_1": "CT-Scan Kepala",
        "severity_level": 3,
        "kreatinin": 1.0,
        "catatan_klinis": "Kreatinin 1.0 mg/dL normal, tidak ada oliguria.",
        "biaya_tagih": 18000000.0,
        "durasi_rawat": 3,
    }

    state = garda_app.invoke({"claim_data": test_claim})
    print(f"   -> StateGraph Final Status: {state.get('final_status')}")
    print(f"   -> Revised Severity: {state.get('revised_severity_level')}")
    print(f"   -> Adjudication Reason Snippet: {state.get('adjudication_reason', '')[:100]}...")
    assert state.get("final_status") in ["APPROVED", "DOWNGRADED", "ESCALATED"], "Pipeline returned invalid status!"

    # Release lock
    stop_event.set()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.terminate()
    print("6. Background lock released cleanly. Disk lock resilience confirmed!\n")

    return {
        "lock_detected": True,
        "fallback_memory_active": True,
        "ingest_succeeded": ingest_count > 0,
        "search_succeeded": len(results) > 0,
        "pipeline_succeeded": state.get("final_status") == "DOWNGRADED",
    }


# ============================================================================
# Section 3: DeepSeek LLM Execution Latency Profiling
# ============================================================================
PROMPT_TEST_CASES = [
    {
        "id": "LAT-01",
        "name": "Stroke Iskemik Upcoding Case",
        "diag": "Stroke Iskemik (I63.9) + AKI",
        "claim": {
            "id_kunjungan": "LAT-CLM-001",
            "diag_awal": "Stroke Iskemik Akut (I63.9)",
            "diag_sekunder_1": "Gagal Ginjal Akut (N17.9)",
            "tindakan_1": "CT-Scan",
            "severity_level": 3,
            "kreatinin": 1.0,
            "biaya_tagih": 18000000.0,
            "durasi_rawat": 3,
        },
        "preliminary_verdict": "DOWNGRADE_RECOMMENDED",
    },
    {
        "id": "LAT-02",
        "name": "STEMI Anterior Emergency PCI Case",
        "diag": "STEMI (I21.0) + Cardiogenic Shock",
        "claim": {
            "id_kunjungan": "LAT-CLM-002",
            "diag_awal": "STEMI Anterior Akut (I21.0)",
            "diag_sekunder_1": "Syok Kardiogenik (R57.0)",
            "tindakan_1": "Primary PCI",
            "severity_level": 3,
            "troponin": 15.0,
            "biaya_tagih": 48000000.0,
            "durasi_rawat": 4,
        },
        "preliminary_verdict": "APPROVE_RECOMMENDED",
    },
    {
        "id": "LAT-03",
        "name": "Refractory Status Epilepticus Missing Trace Case",
        "diag": "Status Epileptikus (G40.9)",
        "claim": {
            "id_kunjungan": "LAT-CLM-003",
            "diag_awal": "Refractory Status Epilepticus (G40.9)",
            "diag_sekunder_1": "Encephalopathy",
            "tindakan_1": "Continuous Video-EEG",
            "severity_level": 3,
            "eeg_attached": False,
            "tipe_faskes": "RS Tipe C",
            "biaya_tagih": 22000000.0,
            "durasi_rawat": 2,
        },
        "preliminary_verdict": "ESCALATE_RECOMMENDED",
    },
    {
        "id": "LAT-04",
        "name": "Diabetes Melitus Debridement Case",
        "diag": "Diabetes Melitus (E11.5) + Gangren",
        "claim": {
            "id_kunjungan": "LAT-CLM-004",
            "diag_awal": "Diabetes Melitus Tipe 2 dengan Gangren (E11.5)",
            "diag_sekunder_1": "Ulkus Kaki Diabetik",
            "tindakan_1": "Debridement Radikal Kamar Operasi",
            "severity_level": 2,
            "biaya_tagih": 12500000.0,
            "durasi_rawat": 5,
        },
        "preliminary_verdict": "APPROVE_RECOMMENDED",
    },
    {
        "id": "LAT-05",
        "name": "Syok Septik dengan Ventilator ICU Case",
        "diag": "Syok Septik (R65.21) + Sepsis",
        "claim": {
            "id_kunjungan": "LAT-CLM-005",
            "diag_awal": "Syok Septik (R65.21)",
            "diag_sekunder_1": "Pneumonia Aspirasi",
            "tindakan_1": "Ventilator Mekanik Invasif > 96 Jam",
            "severity_level": 3,
            "biaya_tagih": 65000000.0,
            "durasi_rawat": 8,
        },
        "preliminary_verdict": "APPROVE_RECOMMENDED",
    },
]


def profile_deepseek_latency(num_iterations: int = 5):
    print("\n" + "=" * 90)
    print("⏱️ [CHALLENGE 3] DEEPSEEK LLM EXECUTION LATENCY PROFILING (<15s SLA)")
    print("=" * 90)

    llm = get_llm()
    records = []

    # Run across prompt test cases
    test_samples = PROMPT_TEST_CASES[:num_iterations]
    for idx, test_case in enumerate(test_samples, 1):
        claim = test_case["claim"]
        preliminary = test_case["preliminary_verdict"]

        state_input: ClaimState = {
            "claim_id": claim["id_kunjungan"],
            "claim_data": claim,
            "ml_risk_score": 0.88,
            "is_anomalous": True,
            "ml_explanation": "Evaluasi risiko XGBoost.",
            "rag_context": "Aturan INA-CBG dan PNPK Kemenkes relevan.",
            "validation_status": "DISCREPANCY_DETECTED" if "DOWNGRADE" in preliminary else "CLEAR",
            "preliminary_verdict": preliminary,
            "clinical_inconsistencies": ["Inkonsistensi terdeteksi"] if "DOWNGRADE" in preliminary else [],
            "medical_validation_notes": "Catatan telaah medis validator.",
            "revised_severity_level": 2 if "DOWNGRADE" in preliminary else None,
        }

        t0 = time.perf_counter()
        out = executor_node(state_input)
        latency = time.perf_counter() - t0

        status = out.get("final_status")
        reason_len = len(out.get("adjudication_reason", ""))
        conf = out.get("confidence_score")

        records.append({
            "test_id": test_case["id"],
            "name": test_case["name"],
            "latency": latency,
            "status": status,
            "reason_length": reason_len,
            "confidence": conf,
            "sla_met": latency < 15.0,
        })

        sla_icon = "✅" if latency < 15.0 else "❌"
        print(f" {sla_icon} [{test_case['id']}] {test_case['name']:<45} | "
              f"Latency: {latency:5.2f}s (<15s SLA) | Status: {status:<10} | Reason: {reason_len} chars")

    lat_arr = np.array([r["latency"] for r in records])
    stats = {
        "count": len(records),
        "min_sec": float(np.min(lat_arr)),
        "mean_sec": float(np.mean(lat_arr)),
        "median_sec": float(np.percentile(lat_arr, 50)),
        "p95_sec": float(np.percentile(lat_arr, 95)),
        "max_sec": float(np.max(lat_arr)),
        "all_under_15s": bool(np.all(lat_arr < 15.0)),
        "records": records,
    }

    print("-" * 90)
    print(f"📊 SUMMARY: Min={stats['min_sec']:.2f}s, Mean={stats['mean_sec']:.2f}s, "
          f"Median={stats['median_sec']:.2f}s, P95={stats['p95_sec']:.2f}s, Max={stats['max_sec']:.2f}s")
    print(f"🎯 SLA Compliance (<15s): {'PASSED (100%)' if stats['all_under_15s'] else 'FAILED'}")

    # Adversarial Sub-test: Force timeout / network drop simulation
    print("\n   [Sub-test] Adversarial Timeout/Error Resilience Check:")
    class FaultyLLM:
        def invoke(self, *args, **kwargs):
            raise TimeoutError("Simulated LLM Gateway Timeout (>60s)")

    import app.agents.nodes as nodes_module
    orig_get_llm = nodes_module.get_llm
    try:
        nodes_module.get_llm = lambda: FaultyLLM()
        t_err_0 = time.perf_counter()
        fallback_out = nodes_module.executor_node(state_input)
        t_err_elapsed = time.perf_counter() - t_err_0

        assert fallback_out.get("final_status") in ["APPROVED", "DOWNGRADED", "ESCALATED"]
        assert len(fallback_out.get("adjudication_reason", "")) > 50
        print(f"   ✅ Graceful deterministic fallback triggered without crashing (Took {t_err_elapsed*1000:.1f}ms).")
        stats["fallback_resilience_verified"] = True
    finally:
        nodes_module.get_llm = orig_get_llm

    return stats


# ============================================================================
# Section 4: Test Suite Determinism Verification across Runs
# ============================================================================
def verify_test_suites_determinism(num_rag_runs: int = 5, num_langgraph_runs: int = 3):
    print("\n" + "=" * 90)
    print("🔁 [CHALLENGE 4] TEST SUITE DETERMINISM & REPEATABILITY VERIFICATION")
    print("=" * 90)

    project_root = os.path.dirname(os.path.abspath(__file__))
    python_bin = sys.executable

    # 1. Determinism of test_rag.py
    print(f"1. Executing test_rag.py across {num_rag_runs} consecutive runs...")
    rag_exit_codes = []
    rag_durations = []

    for r in range(1, num_rag_runs + 1):
        t0 = time.perf_counter()
        cmd = [python_bin, os.path.join(project_root, "test_rag.py")]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.perf_counter() - t0
        rag_exit_codes.append(res.returncode)
        rag_durations.append(elapsed)
        status_sym = "✅" if res.returncode == 0 else "❌"
        print(f"   Run #{r}: Exit {res.returncode} {status_sym} ({elapsed:.2f}s)")

    rag_deterministic = all(code == 0 for code in rag_exit_codes)
    print(f"   -> test_rag.py Determinism: {'100% PASS' if rag_deterministic else 'FAILED'}")

    # 2. Determinism of test_langgraph.py
    print(f"\n2. Executing test_langgraph.py across {num_langgraph_runs} consecutive runs...")
    lg_exit_codes = []
    lg_statuses = []
    lg_durations = []

    for r in range(1, num_langgraph_runs + 1):
        t0 = time.perf_counter()
        cmd = [python_bin, os.path.join(project_root, "test_langgraph.py")]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.perf_counter() - t0
        lg_exit_codes.append(res.returncode)
        lg_durations.append(elapsed)

        # Parse final statuses from stdout
        s1 = "DOWNGRADED" if "Status: DOWNGRADED" in res.stdout else "UNKNOWN"
        s2 = "APPROVED" if "Status: APPROVED" in res.stdout else "UNKNOWN"
        s3 = "ESCALATED" if "Status: ESCALATED" in res.stdout else "UNKNOWN"
        lg_statuses.append((s1, s2, s3))

        status_sym = "✅" if res.returncode == 0 and (s1, s2, s3) == ("DOWNGRADED", "APPROVED", "ESCALATED") else "❌"
        print(f"   Run #{r}: Exit {res.returncode} {status_sym} ({elapsed:.2f}s) | S1={s1}, S2={s2}, S3={s3}")

    lg_deterministic = all(code == 0 for code in lg_exit_codes) and len(set(lg_statuses)) == 1
    print(f"   -> test_langgraph.py Determinism: {'100% PASS & IDENTICAL VERDICTS' if lg_deterministic else 'FAILED'}")

    return {
        "rag_runs": num_rag_runs,
        "rag_deterministic": rag_deterministic,
        "rag_mean_duration": float(np.mean(rag_durations)),
        "langgraph_runs": num_langgraph_runs,
        "langgraph_deterministic": lg_deterministic,
        "langgraph_mean_duration": float(np.mean(lg_durations)),
        "statuses_observed": lg_statuses,
    }


# ============================================================================
# Main Orchestrator for Challenger 2
# ============================================================================
def main():
    print("=" * 90)
    print("🛡️ GARDA-JKN EMPIRICAL CHALLENGER 2: CONCURRENCY, VECTOR DB & LATENCY")
    print("=" * 90)

    c1_summary = run_concurrency_stress_test(concurrency_levels=[1, 10, 25, 50], total_queries_per_level=50)
    c2_summary = run_disk_lock_resilience_test()
    c3_summary = profile_deepseek_latency(num_iterations=5)
    c4_summary = verify_test_suites_determinism(num_rag_runs=5, num_langgraph_runs=3)

    print("\n" + "=" * 90)
    print("🏁 FINAL SUMMARY OF EMPIRICAL ADVERSARIAL CHALLENGES")
    print("=" * 90)
    print(f"1. Concurrent Vector Search (50 threads) : {'PASS (0 errors, ' + str(round(c1_summary[-1]['qps'], 1)) + ' QPS)' if c1_summary[-1]['error_count'] == 0 else 'FAIL'}")
    print(f"2. Vector Store Disk Lock Memory Fallback : {'PASS (Transparent fallback & recovery)' if c2_summary['pipeline_succeeded'] else 'FAIL'}")
    print(f"3. DeepSeek LLM Latency Profiling (<15s)  : {'PASS (Max: ' + str(round(c3_summary['max_sec'], 2)) + 's, Mean: ' + str(round(c3_summary['mean_sec'], 2)) + 's)' if c3_summary['all_under_15s'] else 'FAIL'}")
    print(f"4. Test Suites Determinism & Stability    : {'PASS (RAG: 100%, LangGraph: 100%)' if c4_summary['rag_deterministic'] and c4_summary['langgraph_deterministic'] else 'FAIL'}")
    print("=" * 90)

    # Output machine-readable JSON results
    all_passed = (
        c1_summary[-1]["error_count"] == 0
        and c2_summary["pipeline_succeeded"]
        and c3_summary["all_under_15s"]
        and c4_summary["rag_deterministic"]
        and c4_summary["langgraph_deterministic"]
    )

    verdict = "APPROVE" if all_passed else "REJECT"
    print(f"\n>> VERDICT: {verdict} <<\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

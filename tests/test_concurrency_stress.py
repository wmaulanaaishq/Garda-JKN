"""GARDA-JKN Concurrency, Throughput, and Latency Stress-Testing Suite.

Target Endpoint: POST /api/v1/adjudicate
Milestone: Concurrency & Throughput Stress Verification
Components Verified:
1. Multi-threaded XGBoost & SHAP TreeExplainer inference
2. Multi-threaded Qdrant Vector DB querying & storage integrity
3. Live ASGI Uvicorn HTTP server concurrency (5, 10, 20 parallel threads)
4. Memory stability & leak detection via Linux /proc VmRSS profiling
5. Response contract enforcement & latency percentiles (p50, p95, p99)
"""

import concurrent.futures
import json
import logging
import os
import socket
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import httpx
import numpy as np
import pytest

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api import EvaluationResponse  # noqa: E402
from app.core.ml_engine import ml_engine  # noqa: E402
from app.core.vector_db import MedicalKnowledgeBase  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("concurrency_stress")

# Suppress noisy external logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)


# ============================================================================
# Test Payloads Catalog: Complex, Diverse Real-World Medical Claims
# ============================================================================
COMPLEX_CLAIMS = [
    {
        "id_kunjungan": "BURST-STR-001",
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
        "kreatinin": 1.0,
        "catatan_klinis": "Kreatinin 1.0 mg/dL normal, tidak ada oliguria.",
    },
    {
        "id_kunjungan": "BURST-SEP-002",
        "nama_pasien": "Bambang Haryanto",
        "nik": "3175021208650004",
        "usia": 59,
        "diag_awal": "Sepsis Berat (A41.9)",
        "diag_sekunder_1": "Syok Septik (R57.2)",
        "diag_sekunder_2": "Asidosis Metabolik (E87.2)",
        "tindakan_1": "Injeksi Antibiotik Spektrum Luas",
        "tindakan_2": "Infus Vasopresor",
        "icu_days": 0,
        "severity_level": 3,
        "biaya_tagih": 48000000.0,
        "durasi_rawat": 1,
        "catatan_klinis": "Klaim sepsis syok namun 0 hari ICU.",
    },
    {
        "id_kunjungan": "BURST-CRD-003",
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
        "catatan_klinis": "Door to balloon 60 menit, elevasi troponin masif.",
    },
    {
        "id_kunjungan": "BURST-PNE-004",
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
        "catatan_klinis": "Ventilator invasif > 96 jam di ICU.",
    },
    {
        "id_kunjungan": "BURST-EPI-005",
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
        "catatan_klinis": "Faskes tipe C tanpa strip trace EEG autentik.",
    },
    {
        "id_kunjungan": "BURST-ONC-006",
        "nama_pasien": "Soeprapto Martodihardjo",
        "nik": "3171010101450001",
        "usia": 78,
        "diag_awal": "Leukemia Limfoblastik Akut (C91.0)",
        "diag_sekunder_1": "Malnutrisi Energi Protein Berat (E43)",
        "diag_sekunder_2": "Gagal Ginjal Akut (N17.9)",
        "tindakan_1": "Kemoterapi Induksi Terjadwal",
        "tindakan_2": "Hemodialisis Cito",
        "icu_days": 4,
        "severity_level": 3,
        "biaya_tagih": 75000000.0,
        "durasi_rawat": 14,
        "catatan_klinis": (
            "Geriatri onkologi risiko tinggi dengan pansitopenia berat."
        ),
    },
]

CLINICAL_RAG_QUERIES = [
    "Batas waktu pemberian trombolisis rTPA pada stroke iskemik akut",
    "Target waktu door to balloon tindakan PCI primer dan batas LOS STEMI",
    "Indikasi tindakan bedah debridement pada ulkus diabetes melitus",
    "Kapan klaim Severity Level III dianggap upcoding dan harus didowngrade?",
    "Kriteria laboratorium KDIGO untuk penegakan komorbiditas gagal ginjal",
    "Persyaratan lampiran strip trace EEG kontinu pada faskes tipe C",
    "Tatalaksana syok kardiogenik dengan elevasi segmen ST dan hipotensi",
    "Standar koding INA-CBG untuk pemakaian ventilator mekanik invasif",
]


# ============================================================================
# Linux Memory & Resource Profiler
# ============================================================================
def get_process_rss_mb(pid: Optional[int] = None) -> float:
    """Reads VmRSS directly from Linux /proc filesystem in Megabytes."""
    path = "/proc/self/status" if pid is None else f"/proc/{pid}/status"
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    return float(parts[1]) / 1024.0  # kB to MB
    except Exception:
        return 0.0
    return 0.0


# ============================================================================
# Section 1: Concurrent XGBoost & SHAP Inference Stress
# ============================================================================
def execute_single_ml_prediction(
    claim_dict: Dict[str, Any]
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        pred = ml_engine.predict_risk(claim_dict)
        elapsed = time.perf_counter() - t0
        prob = pred.get("risk_score", 0.0)
        is_anom = pred.get("is_anomaly", False)
        expl = pred.get("explanation", "")
        valid = (
            isinstance(prob, (float, int))
            and 0.0 <= prob <= 1.0
            and isinstance(is_anom, bool)
            and len(expl) > 0
        )
        return {
            "latency": elapsed,
            "valid": valid,
            "error": None,
            "prob": prob,
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {
            "latency": elapsed,
            "valid": False,
            "error": str(e),
            "prob": 0.0,
        }


def run_xgboost_concurrency_stress(
    concurrency_workers: Optional[List[int]] = None,
    iterations_per_level: int = 50,
) -> Dict[str, Any]:
    if concurrency_workers is None:
        concurrency_workers = [5, 10, 20, 30]
    logger.info("Executing XGBoost & SHAP multi-threaded stress test...")
    results = {}

    for workers in concurrency_workers:
        tasks = [
            COMPLEX_CLAIMS[i % len(COMPLEX_CLAIMS)]
            for i in range(iterations_per_level)
        ]
        latencies = []
        errors = []
        valid_count = 0

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=workers
        ) as executor:
            futures = [
                executor.submit(execute_single_ml_prediction, claim)
                for claim in tasks
            ]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                latencies.append(res["latency"])
                if res["error"]:
                    errors.append(res["error"])
                if res["valid"]:
                    valid_count += 1

        total_time = time.perf_counter() - t_start
        lat_arr = np.array(latencies)

        stats = {
            "workers": workers,
            "total_requests": len(tasks),
            "valid_requests": valid_count,
            "error_count": len(errors),
            "duration_sec": total_time,
            "qps": len(tasks) / total_time if total_time > 0 else 0,
            "min_ms": float(np.min(lat_arr) * 1000),
            "p50_ms": float(np.percentile(lat_arr, 50) * 1000),
            "p95_ms": float(np.percentile(lat_arr, 95) * 1000),
            "p99_ms": float(np.percentile(lat_arr, 99) * 1000),
            "max_ms": float(np.max(lat_arr) * 1000),
            "mean_ms": float(np.mean(lat_arr) * 1000),
        }
        results[f"workers_{workers}"] = stats
        logger.info(
            f"[XGBoost Stress] Workers: {workers:2d} | "
            f"QPS: {stats['qps']:6.1f} | p50: {stats['p50_ms']:5.1f}ms | "
            f"p95: {stats['p95_ms']:5.1f}ms | Errors: {len(errors)}"
        )

    return results


# ============================================================================
# Section 2: Concurrent Qdrant Vector DB Querying & Lock Resilience
# ============================================================================
def execute_single_qdrant_query(
    kb: MedicalKnowledgeBase, query: str
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        results = kb.search_rules(query, top_k=3)
        elapsed = time.perf_counter() - t0
        valid = isinstance(results, list) and (
            len(results) == 0 or hasattr(results, "get_sources")
        )
        return {
            "latency": elapsed,
            "valid": valid,
            "count": len(results),
            "error": None,
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {
            "latency": elapsed,
            "valid": False,
            "count": 0,
            "error": str(e),
        }


def run_qdrant_concurrency_stress(
    concurrency_workers: Optional[List[int]] = None,
    iterations_per_level: int = 30,
) -> Dict[str, Any]:
    if concurrency_workers is None:
        concurrency_workers = [5, 10, 20]
    logger.info("Executing Qdrant Vector DB multi-threaded querying test...")
    kb = MedicalKnowledgeBase()
    kb.connect()

    initial_info = kb.get_collection_info()
    initial_points = initial_info.get("points_count", 0)
    results = {"initial_points": initial_points}

    for workers in concurrency_workers:
        queries = [
            CLINICAL_RAG_QUERIES[i % len(CLINICAL_RAG_QUERIES)]
            for i in range(iterations_per_level)
        ]
        latencies = []
        errors = []
        valid_count = 0

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=workers
        ) as executor:
            futures = [
                executor.submit(execute_single_qdrant_query, kb, q)
                for q in queries
            ]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                latencies.append(res["latency"])
                if res["error"]:
                    errors.append(res["error"])
                if res["valid"]:
                    valid_count += 1

        total_time = time.perf_counter() - t_start
        lat_arr = np.array(latencies)

        stats = {
            "workers": workers,
            "total_requests": len(queries),
            "valid_requests": valid_count,
            "error_count": len(errors),
            "duration_sec": total_time,
            "qps": len(queries) / total_time if total_time > 0 else 0,
            "min_ms": float(np.min(lat_arr) * 1000),
            "p50_ms": float(np.percentile(lat_arr, 50) * 1000),
            "p95_ms": float(np.percentile(lat_arr, 95) * 1000),
            "p99_ms": float(np.percentile(lat_arr, 99) * 1000),
            "max_ms": float(np.max(lat_arr) * 1000),
            "mean_ms": float(np.mean(lat_arr) * 1000),
        }
        results[f"workers_{workers}"] = stats
        logger.info(
            f"[Qdrant Stress] Workers: {workers:2d} | QPS: {stats['qps']:6.1f}"
            f" | p50: {stats['p50_ms']:5.1f}ms | p95: {stats['p95_ms']:5.1f}ms"
            f" | Errors: {len(errors)}"
        )

    # Verify storage integrity post-stress
    post_info = kb.get_collection_info()
    post_points = post_info.get("points_count", 0)
    results["post_points"] = post_points
    results["integrity_preserved"] = (post_points == initial_points)
    assert results["integrity_preserved"], (
        f"Altered! Before: {initial_points}, After: {post_points}"
    )

    return results


# ============================================================================
# Section 3: Live ASGI Uvicorn Server Multi-Threaded HTTP Adjudication Stress
# ============================================================================
def execute_single_http_adjudication(
    client: httpx.Client,
    base_url: str,
    payload: Dict[str, Any],
    req_id: int,
) -> Dict[str, Any]:
    url = f"{base_url}/api/v1/adjudicate"
    t0 = time.perf_counter()
    try:
        resp = client.post(url, json=payload, timeout=60.0)
        elapsed = time.perf_counter() - t0
        status_code = resp.status_code

        if status_code != 200:
            return {
                "req_id": req_id,
                "latency": elapsed,
                "status_code": status_code,
                "valid": False,
                "error": f"HTTP {status_code}: {resp.text[:200]}",
                "adjudication_result": None,
                "severity_level": None,
                "confidence_score": None,
            }

        data = resp.json()
        val_resp = EvaluationResponse.model_validate(data)

        detail = data.get("response", {})
        adj_val = data.get("adjudication_result")
        adj_result = adj_val or detail.get("adjudication_result")
        sev_level = (
            data.get("severity_level")
            if "severity_level" in data
            else detail.get("severity_level")
        )
        conf_score = (
            data.get("confidence_score")
            if "confidence_score" in data
            else detail.get("confidence_score")
        )
        ml_risk = detail.get("ml_risk_score")
        is_anom = detail.get("is_anomalous")
        adj_reason = detail.get("adjudication_reason", "")

        is_valid = (
            val_resp.success is True
            and adj_result in ["APPROVED", "DOWNGRADED", "ESCALATED"]
            and sev_level in [1, 2, 3]
            and isinstance(conf_score, (float, int))
            and 0.0 <= conf_score <= 1.0
            and isinstance(ml_risk, (float, int))
            and isinstance(is_anom, bool)
            and len(adj_reason) > 20
        )

        return {
            "req_id": req_id,
            "latency": elapsed,
            "status_code": 200,
            "valid": is_valid,
            "error": None if is_valid else "Contract validation failed",
            "adjudication_result": adj_result,
            "severity_level": sev_level,
            "confidence_score": conf_score,
            "decision": detail.get("decision"),
        }
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {
            "req_id": req_id,
            "latency": elapsed,
            "status_code": 0,
            "valid": False,
            "error": str(e),
            "adjudication_result": None,
            "severity_level": None,
            "confidence_score": None,
        }


def run_live_http_concurrency_stress(
    base_url: str, server_pid: Optional[int] = None
) -> Dict[str, Any]:
    """Runs empirical multi-threaded bursts against live endpoint."""
    logger.info("Executing Live HTTP Concurrency & Throughput Stress...")

    concurrency_stages = [
        {"name": "Stage 1: Baseline Warmup", "workers": 1, "requests": 2},
        {"name": "Stage 2: Moderate Burst", "workers": 5, "requests": 10},
        {"name": "Stage 3: High Concurrency", "workers": 10, "requests": 20},
        {"name": "Stage 4: Peak Stress Burst", "workers": 20, "requests": 40},
    ]

    all_stage_metrics = []
    initial_rss = get_process_rss_mb(server_pid)
    peak_rss = initial_rss

    for stage in concurrency_stages:
        workers = stage["workers"]
        total_reqs = stage["requests"]
        stage_name = stage["name"]
        logger.info(
            f"--- Running {stage_name} "
            f"({workers} threads, {total_reqs} reqs) ---"
        )

        tasks = [
            COMPLEX_CLAIMS[i % len(COMPLEX_CLAIMS)]
            for i in range(total_reqs)
        ]
        latencies = []
        errors = []
        valid_count = 0
        status_codes = {}
        decisions = {}

        t_stage_start = time.perf_counter()

        def _worker_fn(claim_payload, req_idx):
            with httpx.Client() as client:
                return execute_single_http_adjudication(
                    client, base_url, claim_payload, req_idx
                )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=workers
        ) as executor:
            futures = [
                executor.submit(_worker_fn, payload, i)
                for i, payload in enumerate(tasks)
            ]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                latencies.append(res["latency"])
                sc = res["status_code"]
                status_codes[sc] = status_codes.get(sc, 0) + 1
                if res["adjudication_result"]:
                    d = res["adjudication_result"]
                    decisions[d] = decisions.get(d, 0) + 1
                if res["error"]:
                    errors.append(res["error"])
                if res["valid"]:
                    valid_count += 1

                # Profile memory during execution
                current_rss = get_process_rss_mb(server_pid)
                if current_rss > peak_rss:
                    peak_rss = current_rss

        total_stage_duration = time.perf_counter() - t_stage_start
        lat_arr = np.array(latencies)

        metrics = {
            "stage_name": stage_name,
            "workers": workers,
            "total_requests": total_reqs,
            "valid_requests": valid_count,
            "success_rate_pct": (
                (valid_count / total_reqs) * 100.0 if total_reqs > 0 else 0.0
            ),
            "error_count": len(errors),
            "errors": errors[:5],
            "duration_sec": total_stage_duration,
            "qps": (
                total_reqs / total_stage_duration
                if total_stage_duration > 0
                else 0
            ),
            "min_sec": float(np.min(lat_arr)),
            "p50_sec": float(np.percentile(lat_arr, 50)),
            "p90_sec": float(np.percentile(lat_arr, 90)),
            "p95_sec": float(np.percentile(lat_arr, 95)),
            "p99_sec": float(np.percentile(lat_arr, 99)),
            "max_sec": float(np.max(lat_arr)),
            "mean_sec": float(np.mean(lat_arr)),
            "std_sec": float(np.std(lat_arr)),
            "status_distribution": status_codes,
            "decision_distribution": decisions,
        }
        all_stage_metrics.append(metrics)

        logger.info(
            f"Completed {stage_name}: {valid_count}/{total_reqs} OK | "
            f"Dur: {total_stage_duration:5.2f}s | QPS: {metrics['qps']:4.2f}\n"
            f"  p50: {metrics['p50_sec']:5.2f}s | "
            f"p95: {metrics['p95_sec']:5.2f}s | "
            f"max: {metrics['max_sec']:5.2f}s"
        )

    final_rss = get_process_rss_mb(server_pid)

    return {
        "stages": all_stage_metrics,
        "memory_profile": {
            "initial_rss_mb": initial_rss,
            "peak_rss_mb": peak_rss,
            "final_rss_mb": final_rss,
            "rss_delta_mb": final_rss - initial_rss,
        },
    }


# ============================================================================
# Pytest Test Cases for CI / Automated Verification
# ============================================================================
@pytest.fixture(scope="module")
def live_server():
    """Spins up dynamic uvicorn server on dynamic port for HTTP testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        ephemeral_port = s.getsockname()[1]

    python_bin = os.path.abspath(os.path.join(PROJECT_ROOT, "venv", "bin"))
    env = os.environ.copy()
    env["PORT"] = str(ephemeral_port)
    env["PATH"] = f"{python_bin}:{env.get('PATH', '')}"

    proc = subprocess.Popen(
        f'sh -c "uvicorn api:app --host 127.0.0.1 --port {ephemeral_port}"',
        shell=True,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{ephemeral_port}"
    server_ready = False
    start_time = time.time()

    try:
        while time.time() - start_time < 60:
            try:
                resp = httpx.get(f"{base_url}/health", timeout=1.0)
                if (
                    resp.status_code == 200
                    and resp.json().get("status") == "healthy"
                ):
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.5)

        assert server_ready, (
            f"Server failed to spin up on port {ephemeral_port}"
        )
        yield {"base_url": base_url, "port": ephemeral_port, "pid": proc.pid}

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_xgboost_shap_concurrent_inference():
    """Verify XGBoost + SHAP operates safely across 5, 10, 20, 30 workers."""
    res = run_xgboost_concurrency_stress(
        concurrency_workers=[5, 10, 20, 30], iterations_per_level=40
    )
    for workers_key, stats in res.items():
        assert stats["error_count"] == 0, (
            f"Errors in {workers_key}: {stats['error_count']}"
        )
        assert stats["valid_requests"] == stats["total_requests"]
        assert stats["p95_ms"] < 2000.0, (
            f"XGBoost p95 too high: {stats['p95_ms']}ms"
        )


def test_qdrant_vector_db_concurrent_queries():
    """Verify Qdrant disk collection handles concurrent queries safely."""
    res = run_qdrant_concurrency_stress(
        concurrency_workers=[5, 10, 20], iterations_per_level=25
    )
    assert res["integrity_preserved"] is True
    for workers in [5, 10, 20]:
        stats = res[f"workers_{workers}"]
        assert stats["error_count"] == 0, (
            f"Qdrant query errors: {stats['error_count']}"
        )
        assert stats["valid_requests"] == stats["total_requests"]


def test_live_http_adjudication_concurrency_and_latency(live_server):
    """Stress-test live POST /api/v1/adjudicate under 5, 10, 20 threads."""
    benchmark = run_live_http_concurrency_stress(
        base_url=live_server["base_url"],
        server_pid=live_server["pid"],
    )

    stages = benchmark["stages"]
    assert len(stages) == 4

    for st in stages:
        assert st["error_count"] == 0, (
            f"Errors in stage {st['stage_name']}: {st['errors']}"
        )
        assert st["success_rate_pct"] == 100.0
        assert 200 in st["status_distribution"]
        assert st["status_distribution"][200] == st["total_requests"]

    peak_stage = stages[-1]
    assert peak_stage["workers"] == 20
    assert peak_stage["total_requests"] == 40
    assert peak_stage["valid_requests"] == 40

    mem = benchmark["memory_profile"]
    assert mem["rss_delta_mb"] < 500.0, (
        f"Potential memory leak detected: delta={mem['rss_delta_mb']}MB"
    )


# ============================================================================
# Standalone CLI Runner for Benchmarking & Report Generation
# ============================================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="GARDA-JKN Concurrency Stress Harness"
    )
    parser.add_argument(
        "--url", type=str, default=None, help="Base URL of live server"
    )
    parser.add_argument(
        "--pid", type=int, default=None, help="Server process ID for memory"
    )
    args = parser.parse_args()

    print("=" * 90)
    print("🚀 GARDA-JKN EMPIRICAL CONCURRENCY & THROUGHPUT STRESS HARNESS")
    print("=" * 90)

    # 1. XGBoost & SHAP stress
    print("\n[Phase 1] Multi-Threaded XGBoost & SHAP Stress Testing...")
    xgb_results = run_xgboost_concurrency_stress(
        concurrency_workers=[5, 10, 20, 30], iterations_per_level=50
    )

    # 2. Qdrant Vector DB stress
    print("\n[Phase 2] Multi-Threaded Qdrant Querying & Lock Resilience...")
    qdrant_results = run_qdrant_concurrency_stress(
        concurrency_workers=[5, 10, 20], iterations_per_level=30
    )

    # 3. Live ASGI HTTP Server Stress
    print("\n[Phase 3] Live ASGI Uvicorn HTTP Server Concurrency Stress...")
    base_url = args.url
    server_pid = args.pid
    spawned_proc = None

    if not base_url:
        # Check if default ports are running
        for candidate_port in [9876, 8000]:
            candidate_url = f"http://127.0.0.1:{candidate_port}"
            try:
                r = httpx.get(f"{candidate_url}/health", timeout=1.0)
                if r.status_code == 200:
                    base_url = candidate_url
                    print(f"Discovered active server at {base_url}")
                    break
            except Exception:
                pass

    if not base_url:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            ephemeral_port = s.getsockname()[1]

        python_bin = os.path.abspath(os.path.join(PROJECT_ROOT, "venv", "bin"))
        env = os.environ.copy()
        env["PORT"] = str(ephemeral_port)
        env["PATH"] = f"{python_bin}:{env.get('PATH', '')}"

        cmd_str = (
            f'sh -c "uvicorn api:app --host 127.0.0.1 --port {ephemeral_port}"'
        )
        spawned_proc = subprocess.Popen(
            cmd_str,
            shell=True,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        base_url = f"http://127.0.0.1:{ephemeral_port}"
        server_pid = spawned_proc.pid
        server_ready = False
        start_time = time.time()

        try:
            while time.time() - start_time < 60:
                try:
                    resp = httpx.get(f"{base_url}/health", timeout=1.0)
                    if (
                        resp.status_code == 200
                        and resp.json().get("status") == "healthy"
                    ):
                        server_ready = True
                        break
                except Exception:
                    time.sleep(0.5)

            if not server_ready:
                print("ERROR: Failed to launch Uvicorn server!")
                return 1

        except Exception as e:
            print(f"ERROR: Exception starting server: {e}")
            if spawned_proc:
                spawned_proc.terminate()
            return 1

    try:
        print(f"Running HTTP stress against {base_url} (PID: {server_pid})")
        http_results = run_live_http_concurrency_stress(
            base_url=base_url, server_pid=server_pid
        )
    finally:
        if spawned_proc:
            spawned_proc.terminate()
            try:
                spawned_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                spawned_proc.kill()

    full_benchmark_output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "xgboost_stress": xgb_results,
        "qdrant_stress": qdrant_results,
        "http_concurrency_stress": http_results,
    }

    out_json_path = os.path.join(
        PROJECT_ROOT,
        ".agents",
        "teamwork",
        "challenger_concurrency_stress",
        "raw_benchmark_metrics.json",
    )
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(full_benchmark_output, f, indent=2)

    print("\n" + "=" * 90)
    print(f"✅ Benchmark metrics saved to {out_json_path}")
    print("=" * 90)
    return 0


if __name__ == "__main__":
    sys.exit(main())

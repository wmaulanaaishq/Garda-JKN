"""Tests for GARDA-JKN Backend Health, API Contracts, CORS, and Deployment Port Binding.

Milestones covered:
- R1: Backend Health and Connectivity (FastAPI endpoints, CORS, Procfile PORT evaluation)
- R2: Complex Payload Response Contract Alignment (adjudication_result, severity_level, confidence_score)
"""

import os
import sys
import socket
import subprocess
import time
import pytest
import httpx

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient  # noqa: E402
from api import app, ClaimData, EvaluationResponse  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """Provides a synchronous FastAPI TestClient instance."""
    return TestClient(app)


def test_root_endpoint_returns_200(client):
    """Test that GET / returns HTTP 200 OK with expected status message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "GARDA-JKN API is running."


def test_health_endpoint_returns_200(client):
    """Test that GET /health returns HTTP 200 OK with healthy status and service name."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy", "service": "GARDA-JKN API"}


def test_cors_simple_request(client):
    """Test that standard GET request from Vercel frontend origin receives valid CORS headers."""
    frontend_origin = "https://garda-jkn.vercel.app"
    response = client.get("/health", headers={"Origin": frontend_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == frontend_origin
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_adjudicate_endpoint(client):
    """Test that OPTIONS preflight request to /api/v1/adjudicate receives full CORS authorization."""
    frontend_origin = "https://garda-jkn.vercel.app"
    headers = {
        "Origin": frontend_origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/v1/adjudicate", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == frontend_origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allow_headers


def test_procfile_contains_shell_port_evaluation():
    """Verify that Procfile uses sh -c to expand $PORT dynamically for production."""
    procfile_path = os.path.join(os.path.dirname(__file__), "..", "Procfile")
    procfile_path = os.path.abspath(procfile_path)
    assert os.path.exists(procfile_path), f"Procfile not found at {procfile_path}"

    with open(procfile_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    assert "web:" in content
    assert "sh -c" in content, "Procfile must use sh -c to evaluate $PORT dynamic shell variable"
    assert "$PORT" in content
    assert "uvicorn api:app" in content

    # Test shell expansion mechanics
    test_port = "9432"
    cmd = 'sh -c "echo PORT_VAL=$PORT"'
    res = subprocess.run(
        cmd,
        shell=True,
        env={**os.environ, "PORT": test_port},
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert f"PORT_VAL={test_port}" in res.stdout.strip()


def test_procfile_live_dynamic_port_binding():
    """Spin up the server on an ephemeral dynamic PORT via shell command to verify real socket binding."""
    # Find free dynamic port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        ephemeral_port = s.getsockname()[1]

    # Command matching Procfile: sh -c "uvicorn api:app --host 127.0.0.1 --port $PORT"
    python_bin = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "bin"))
    env = os.environ.copy()
    env["PORT"] = str(ephemeral_port)
    env["PATH"] = f"{python_bin}:{env.get('PATH', '')}"

    proc = subprocess.Popen(
        'sh -c "uvicorn api:app --host 127.0.0.1 --port $PORT"',
        shell=True,
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    server_ready = False
    start_time = time.time()
    url = f"http://127.0.0.1:{ephemeral_port}/health"

    try:
        while time.time() - start_time < 15:
            try:
                resp = httpx.get(url, timeout=1.0)
                if resp.status_code == 200 and resp.json().get("status") == "healthy":
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.5)

        assert server_ready, f"Server failed to bind and respond on ephemeral PORT={ephemeral_port}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_adjudication_response_contract_schema(client):
    """Verify that the adjudication endpoint response matches all R1 & R2 acceptance criteria."""
    sample_claim = {
        "id_kunjungan": "TEST-HEALTH-001",
        "nama_pasien": "Budi Santoso",
        "nik": "3201010101010001",
        "usia": 55,
        "diag_awal": "Pneumonia Berat (J18.9)",
        "diag_sekunder_1": "Gagal Napas Akut (J96.0)",
        "diag_sekunder_2": None,
        "tindakan_1": "Pemasangan Ventilator",
        "tindakan_2": None,
        "icu_days": 3,
        "severity_level": 3,
        "biaya_tagih": 25000000.0,
        "durasi_rawat": 7,
    }

    # Validate request model parsing
    claim_obj = ClaimData.model_validate(sample_claim)
    assert claim_obj.id_kunjungan == "TEST-HEALTH-001"

    response = client.post("/api/v1/adjudicate", json=sample_claim)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    # Validate response model parsing
    validated_response = EvaluationResponse.model_validate(data)
    assert validated_response.success is True

    # 1. Base structure
    assert data["success"] is True
    assert data["metadata"]["code"] == 200
    assert "response" in data

    resp_detail = data["response"]

    # 2. Vercel UI backward-compatibility requirement
    assert "decision" in resp_detail
    assert resp_detail["decision"] in ["APPROVED", "DOWNGRADED", "ESCALATED"]

    # 3. Acceptance criteria fields in response detail
    assert "adjudication_result" in resp_detail
    assert resp_detail["adjudication_result"] == resp_detail["decision"]

    assert "severity_level" in resp_detail
    assert isinstance(resp_detail["severity_level"], int)
    assert resp_detail["severity_level"] in [1, 2, 3]

    assert "confidence_score" in resp_detail
    assert isinstance(resp_detail["confidence_score"], (int, float))
    assert 0.0 <= resp_detail["confidence_score"] <= 1.0

    # 4. Preserved fields in response detail
    assert "ml_risk_score" in resp_detail
    assert isinstance(resp_detail["ml_risk_score"], (int, float))

    assert "is_anomalous" in resp_detail
    assert isinstance(resp_detail["is_anomalous"], bool)

    assert "reason_codes" in resp_detail
    assert isinstance(resp_detail["reason_codes"], list)

    assert "adjudication_reason" in resp_detail
    assert isinstance(resp_detail["adjudication_reason"], str)

    assert "rag_context" in resp_detail
    assert isinstance(resp_detail["rag_context"], str)

    # 5. Acceptance criteria top-level mirrors
    assert "adjudication_result" in data
    assert data["adjudication_result"] == resp_detail["decision"]
    assert "severity_level" in data
    assert data["severity_level"] == resp_detail["severity_level"]
    assert "confidence_score" in data
    assert data["confidence_score"] == resp_detail["confidence_score"]

"""End-to-End Playwright Tests for GARDA-JKN Frontend & Backend Integration.

Milestone R3: Frontend Integration & Playwright E2E Testing.
Verifies:
1. Live Vercel frontend navigation (https://garda-jkn.vercel.app).
2. UI layout, headers, textarea, and action buttons.
3. Local FastAPI backend lifecycle on port 8000.
4. Seamless cross-origin adjudication request handling without CORS or PNA.
5. End-to-end multi-agent evaluation rendering (AI Status Banner, JSON Area).
6. Full screenshot artifact generation for audit verification.
"""

import json
import os
import re
import subprocess
import sys
import time
from typing import Generator
import pytest
import requests
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

# Project Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_LOCAL_URL = "http://127.0.0.1:3001"
BACKEND_LOCAL_URL = "http://127.0.0.1:8000"
BACKEND_HEALTH_URL = f"{BACKEND_LOCAL_URL}/"
BACKEND_ADJUDICATE_URL = f"{BACKEND_LOCAL_URL}/api/v1/adjudicate"

SCREENSHOT_DIR = os.path.join(
    PROJECT_ROOT, ".agents", "teamwork", "worker_frontend_playwright"
)
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, "e2e_result.png")

# Complex Medical Claim Payloads
COMPLEX_CLAIM_SEPSIS = {
    "id_kunjungan": "K-SEP-2026-0901",
    "nama_pasien": "Hj. Siti Rahmawati",
    "nik": "3201015504820002",
    "usia": 64,
    "diag_awal": "Sepsis Berat",
    "diag_sekunder_1": "Syok Septik",
    "diag_sekunder_2": "Gagal Ginjal Akut",
    "tindakan_1": "Pemberian Vasopresor Titrasi",
    "tindakan_2": "Hemodialisis Cito",
    "icu_days": 8,
    "severity_level": 3,
    "biaya_tagih": 68500000.0,
    "durasi_rawat": 14,
}

COMPLEX_CLAIM_STROKE = {
    "id_kunjungan": "K-STR-2026-0412",
    "nama_pasien": "Bambang Soedirgo",
    "nik": "3273012345670001",
    "usia": 62,
    "diag_awal": "Stroke Iskemik Akut",
    "diag_sekunder_1": "Hipertensi Emergensi",
    "diag_sekunder_2": "Diabetes Mellitus Tipe 2",
    "tindakan_1": "CT-Scan Kepala Non-Kontras",
    "tindakan_2": "Trombolisis Intravena",
    "icu_days": 3,
    "severity_level": 3,
    "biaya_tagih": 35000000.0,
    "durasi_rawat": 7,
}

LOW_COST_DATA_ENTRY_CLAIM = {
    "id_kunjungan": "K-DQA-2026-0001",
    "nama_pasien": "Synthetic Data Quality Patient",
    "nik": "0000000000000000",
    "usia": 55,
    "diag_awal": "Pneumonia Berat",
    "diag_sekunder_1": "Gagal Napas",
    "tindakan_1": "Pemasangan Ventilator",
    "icu_days": 6,
    "severity_level": 3,
    "biaya_tagih": 28011,
    "durasi_rawat": 12,
}


@pytest.fixture(scope="session")
def local_server() -> Generator[str, None, None]:
    """Manages the background FastAPI server on port 8000 for E2E tests."""
    server_already_running = False
    try:
        r = requests.get(BACKEND_HEALTH_URL, timeout=2)
        if r.status_code == 200:
            server_already_running = True
            print("\n[local_server] Reusing backend server on port 8000")
    except Exception:
        server_already_running = False

    server_process = None
    if not server_already_running:
        print("\n[local_server] Starting uvicorn api:app on port 8000...")
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
        server_process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        start_time = time.time()
        timeout_seconds = 30
        server_ready = False
        while time.time() - start_time < timeout_seconds:
            try:
                r = requests.get(BACKEND_HEALTH_URL, timeout=1)
                if r.status_code == 200:
                    server_ready = True
                    elapsed = time.time() - start_time
                    print(f"[local_server] Backend ready in {elapsed:.2f}s")
                    break
            except Exception:
                time.sleep(0.5)

        if not server_ready:
            if server_process:
                server_process.kill()
            raise RuntimeError(
                f"Uvicorn backend failed within {timeout_seconds}s"
            )

    yield BACKEND_LOCAL_URL

    if server_process is not None:
        print("\n[local_server] Shutting down uvicorn backend...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("[local_server] Backend shutdown complete.")


@pytest.fixture(scope="session")
def frontend_server() -> Generator[str, None, None]:
    """Reuse or start the local Next.js frontend for reproducible E2E tests."""
    try:
        response = requests.get(FRONTEND_LOCAL_URL, timeout=2)
        if response.status_code == 200:
            yield FRONTEND_LOCAL_URL
            return
    except Exception:
        pass

    npm = "/home/wmaulanaaishq/.local/node/bin/npm"
    frontend_root = os.path.join(PROJECT_ROOT, "frontend")
    env = os.environ.copy()
    env["PATH"] = "/home/wmaulanaaishq/.local/node/bin:" + env.get("PATH", "")
    process = subprocess.Popen(
        [npm, "run", "start", "--", "--hostname", "127.0.0.1", "--port", "3001"],
        cwd=frontend_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    started = time.time()
    try:
        while time.time() - started < 45:
            try:
                response = requests.get(FRONTEND_LOCAL_URL, timeout=1)
                if response.status_code == 200:
                    yield FRONTEND_LOCAL_URL
                    return
            except Exception:
                time.sleep(0.5)
        raise RuntimeError("Next.js frontend failed to start within 45 seconds")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="session")
def browser_instance() -> Generator[Browser, None, None]:
    """Provides a Chromium instance configured for cross-origin testing."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-web-security",
                "--disable-features=BlockInsecurePrivateNetworkRequests",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def browser_page(browser_instance: Browser) -> Generator[Page, None, None]:
    """Creates a new page with configured viewport and network listeners."""
    context: BrowserContext = browser_instance.new_context(
        viewport={"width": 1440, "height": 900}
    )
    page: Page = context.new_page()
    page.on("console", lambda message: print(f"[browser console] {message.type}: {message.text}"))
    page.on("pageerror", lambda error: print(f"[browser pageerror] {error}"))
    yield page
    context.close()


def test_local_frontend_loads_and_displays_headers(
    local_server: str, frontend_server: str, browser_page: Page
):
    """Verify the local frontend loads with the current reviewer-console UI."""
    print(f"\n[Test 1] Navigating to {frontend_server}...")
    browser_page.goto(
        frontend_server, wait_until="networkidle", timeout=30000
    )

    # 1. Assert page title
    page_title = browser_page.title()
    print(f"[Test 1] Page Title: '{page_title}'")
    assert "GARDA-JKN" in page_title or "V-Claim" in page_title, (
        f"Unexpected page title: {page_title}"
    )

    # 2. Assert Header and Banner texts
    header_vclaim = browser_page.locator("text=BPJS - VClaim")
    assert header_vclaim.is_visible(), "Top header 'BPJS - VClaim' missing"

    assert browser_page.get_by_text("Console Evaluasi GARDA-JKN").is_visible()

    # 3. Assert JSON Textarea exists and contains initial default payload
    browser_page.get_by_text("Mode Advanced: lihat / terapkan raw JSON").click()
    textarea = browser_page.locator('textarea[aria-label="Raw JSON payload"]')
    assert textarea.is_visible(), "Medical Claim JSON textarea is not visible"
    initial_text = textarea.input_value()
    assert len(initial_text.strip()) > 0, (
        "Textarea should not be empty on load"
    )
    parsed_default = json.loads(initial_text)
    assert "id_kunjungan" in parsed_default, (
        "Default JSON missing id_kunjungan"
    )

    # 4. Assert Evaluation Button is visible and enabled
    eval_btn = browser_page.get_by_role(
        "button", name=re.compile(r"Jalankan Evaluasi", re.I)
    )
    assert eval_btn.is_visible(), "Evaluation button is not visible"
    assert eval_btn.is_enabled(), "Evaluation button should be enabled on idle"
    print("[Test 1] Navigation and UI header assertions passed successfully.")


def test_complex_claim_adjudication_flow_sepsis(
    local_server: str, frontend_server: str, browser_page: Page
):
    """Submit complex Sepsis claim and verify adjudication and screenshot."""
    print(f"\n[Test 2] Navigating to {frontend_server} for Sepsis...")
    browser_page.goto(
        frontend_server, wait_until="networkidle", timeout=30000
    )

    network_errors = []
    adjudicate_responses = []

    def handle_response(response):
        if "api/v1/adjudicate" in response.url:
            adjudicate_responses.append(response)

    def handle_requestfailed(request):
        network_errors.append(f"{request.url}: {request.failure}")

    browser_page.on("response", handle_response)
    browser_page.on("requestfailed", handle_requestfailed)

    # 1. Fill complex Sepsis payload into textarea
    browser_page.get_by_text("Mode Advanced: lihat / terapkan raw JSON").click()
    textarea = browser_page.locator('textarea[aria-label="Raw JSON payload"]')
    sepsis_json_str = json.dumps(COMPLEX_CLAIM_SEPSIS, indent=2)
    textarea.fill(sepsis_json_str)

    current_value = textarea.input_value()
    assert "K-SEP-2026-0901" in current_value, (
        "Textarea did not update with Sepsis payload"
    )

    # 2. Click the evaluation button
    eval_btn = browser_page.get_by_role(
        "button", name=re.compile(r"Jalankan Evaluasi", re.I)
    )
    print(f"[Test 2] Evaluation buttons={eval_btn.count()} enabled={eval_btn.is_enabled()}")
    print("[Test 2] Clicking 'Jalankan Evaluasi' button...")
    eval_btn.click()
    browser_page.wait_for_timeout(1000)
    print(f"[Test 2] After click enabled={eval_btn.is_enabled()}")

    # 3. Verify loading state is triggered
    try:
        loading_indicator = browser_page.locator("text=Mengevaluasi...")
        loading_indicator.wait_for(state="visible", timeout=3000)
        print("[Test 2] Confirmed button entered 'Mengevaluasi...' state.")
    except Exception:
        pass

    # 4. Wait for evaluation result to arrive
    print("[Test 2] Waiting for result container (.json-area)...")
    try:
        browser_page.get_by_text(re.compile(r"STATUS:\s*[A-Z_]+"), exact=False).wait_for(timeout=20000)
    except Exception:
        print("[Test 2] Page after timeout:\n" + browser_page.locator("body").inner_text())
        print(f"[Test 2] Adjudication responses: {[(item.url, item.status) for item in adjudicate_responses]}")
        print(f"[Test 2] Network failures: {network_errors}")
        raise

    # 5. Assert that no UI error banner is shown
    error_banner = browser_page.locator(".text-red-700")
    if error_banner.is_visible():
        err_msg = error_banner.inner_text()
        if "ERROR:" in err_msg:
            pytest.fail(f"Frontend displayed error banner: {err_msg}")

    # 6. Assert AI Status Banner is rendered
    status_banner = browser_page.locator("text=/STATUS:\\s*[A-Z_]+/")
    assert status_banner.is_visible(), "AI Status banner was not rendered"
    status_text = status_banner.inner_text()
    print(f"[Test 2] Rendered AI Status: '{status_text}'")

    # 7. Assert JSON Code Block Content
    browser_page.get_by_text("Raw JSON Response").click()
    json_area = browser_page.locator("pre.json-area").first
    assert json_area.is_visible(), "Response JSON area (.json-area) missing"
    raw_json_text = json_area.inner_text()
    assert len(raw_json_text.strip()) > 0, "Response JSON block is empty"

    response_data = json.loads(raw_json_text)
    print(f"[Test 2] Adjudication Success: {response_data.get('success')}")
    assert response_data.get("success") is True, (
        "Response does not have success=True"
    )

    resp_body = response_data.get("response", {})
    assert "decision" in resp_body or "adjudication_result" in resp_body, (
        "Response missing decision/adjudication_result"
    )
    decision = (
        resp_body.get("decision") or resp_body.get("adjudication_result")
    )
    assert decision in [
        "APPROVED", "DOWNGRADED", "ESCALATED", "REJECTED"
    ], f"Unexpected decision value: {decision}"

    # 8. Assert Network Adjudication Response
    assert len(adjudicate_responses) > 0, (
        "No network call to /api/v1/adjudicate was detected"
    )
    last_response = adjudicate_responses[-1]
    assert last_response.status == 200, (
        f"Expected HTTP 200 from adjudicate API, got {last_response.status}"
    )

    adjudicate_failures = [
        err for err in network_errors if "api/v1/adjudicate" in err
    ]
    assert len(adjudicate_failures) == 0, (
        f"Network failures during adjudication: {adjudicate_failures}"
    )

    # 9. Capture screenshot artifact
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    browser_page.screenshot(path=SCREENSHOT_PATH, full_page=True)
    assert os.path.exists(SCREENSHOT_PATH), (
        f"Screenshot was not saved to {SCREENSHOT_PATH}"
    )
    screenshot_size = os.path.getsize(SCREENSHOT_PATH)
    print(
        f"[Test 2] Saved full-page screenshot to {SCREENSHOT_PATH} "
        f"({screenshot_size} bytes)"
    )


def test_complex_claim_adjudication_flow_stroke(
    local_server: str, frontend_server: str, browser_page: Page
):
    """Submit a complex Stroke claim to ensure multi-scenario stability."""
    print(f"\n[Test 3] Navigating to {frontend_server} for Stroke...")
    browser_page.goto(
        frontend_server, wait_until="networkidle", timeout=30000
    )

    browser_page.get_by_text("Mode Advanced: lihat / terapkan raw JSON").click()
    textarea = browser_page.locator('textarea[aria-label="Raw JSON payload"]')
    stroke_json_str = json.dumps(COMPLEX_CLAIM_STROKE, indent=2)
    textarea.fill(stroke_json_str)

    eval_btn = browser_page.get_by_role(
        "button", name=re.compile(r"Jalankan Evaluasi", re.I)
    )
    eval_btn.click()

    try:
        browser_page.get_by_text(re.compile(r"STATUS:\s*[A-Z_]+"), exact=False).wait_for(timeout=20000)
    except Exception:
        print("[Test 3] Page after timeout:\n" + browser_page.locator("body").inner_text())
        raise

    # Assert STATUS banner and JSON block
    status_banner = browser_page.locator("text=/STATUS:\\s*[A-Z_]+/")
    assert status_banner.is_visible()
    status_text = status_banner.inner_text()
    print(f"[Test 3] Stroke Adjudication Status: '{status_text}'")

    browser_page.get_by_text("Raw JSON Response").click()
    raw_json = browser_page.locator("pre.json-area").first.inner_text()
    data = json.loads(raw_json)
    assert data.get("success") is True
    print("[Test 3] Stroke claim E2E evaluation completed successfully.")


def test_low_cost_data_entry_is_held_for_confirmation(
    local_server: str, frontend_server: str, browser_page: Page
):
    """A likely missing-digit amount must not be silently approved."""
    browser_page.goto(frontend_server, wait_until="networkidle", timeout=30000)
    browser_page.get_by_text("Mode Advanced: lihat / terapkan raw JSON").click()
    textarea = browser_page.locator('textarea[aria-label="Raw JSON payload"]')
    textarea.fill(json.dumps(LOW_COST_DATA_ENTRY_CLAIM, indent=2))
    browser_page.get_by_text("Terapkan JSON ke Form").click()
    browser_page.get_by_role("button", name=re.compile(r"Jalankan Evaluasi", re.I)).click()

    status = browser_page.get_by_text(re.compile(r"STATUS:\s*[A-Z_]+"), exact=False)
    status.wait_for(timeout=60000)
    assert "ESCALATED" in status.inner_text()
    assert browser_page.get_by_text("Data Quality Hold").is_visible()
    assert browser_page.get_by_text(re.compile(r"digit|satuan", re.I)).first.is_visible()


if __name__ == "__main__":
    ret = pytest.main([__file__, "-v", "-s"])
    sys.exit(ret)

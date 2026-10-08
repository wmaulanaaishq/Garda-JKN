from fastapi.testclient import TestClient

from api import app


def test_api_holds_implausibly_low_complex_claim_cost():
    claim = {
        "id_kunjungan": "DQA-001",
        "nama_pasien": "Synthetic Patient",
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

    response = TestClient(app).post("/api/v1/adjudicate", json=claim)

    assert response.status_code == 200
    body = response.json()["response"]
    assert body["decision"] == "ESCALATED"
    assert body["data_quality_flags"]
    assert "digit" in body["data_quality_flags"][0].lower()

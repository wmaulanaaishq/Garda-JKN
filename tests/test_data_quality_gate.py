from app.agents.nodes import validator_node


def test_missing_digits_in_complex_claim_escalates_for_confirmation():
    state = {
        "claim_data": {
            "biaya_tagih": 28_011,
            "durasi_rawat": 12,
            "icu_days": 6,
            "severity_level": 3,
            "diag_awal": "Pneumonia Berat",
            "diag_sekunder_1": "Gagal Napas",
            "tindakan_1": "Pemasangan Ventilator",
        },
        "ml_risk_score": 0.0055,
        "is_anomalous": False,
    }

    result = validator_node(state)

    assert result["preliminary_verdict"] == "ESCALATE_RECOMMENDED"
    assert result["validation_status"] == "DATA_QUALITY_ERROR"
    assert result["data_quality_flags"]
    assert "digit" in result["data_quality_flags"][0].lower()


def test_plausible_complex_claim_has_no_cost_quality_hold():
    state = {
        "claim_data": {
            "biaya_tagih": 28_000_000,
            "durasi_rawat": 12,
            "icu_days": 6,
            "severity_level": 3,
            "diag_awal": "Pneumonia Berat",
            "diag_sekunder_1": "Gagal Napas",
            "tindakan_1": "Pemasangan Ventilator",
        },
        "ml_risk_score": 0.0055,
        "is_anomalous": False,
    }

    result = validator_node(state)

    assert result["data_quality_flags"] == []
    assert result["preliminary_verdict"] == "APPROVE_RECOMMENDED"

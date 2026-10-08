#!/usr/bin/env python3
"""Validasi Hybrid ML Engine: XGBoost + Rule-Based Fallback."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.ml_engine import MLEngine

engine = MLEngine()
print("="*65)
print("🛡️  GARDA-JKN | Validasi Hybrid ML Engine (Lapis 1)")
print("="*65)
print(f"   XGBoost tersedia  : {engine.xgb_available}")
print(f"   XGBoost degenerate: {engine._xgb_is_degenerate}")
print(f"   SHAP aktif        : {engine.explainer is not None}")
print(f"   Mode scoring      : {'Rule-Based Heuristic (Fallback)' if engine._xgb_is_degenerate else 'XGBoost + SHAP'}")

test_cases = [
    {
        "label": "🏥 Kasus 1 — Klaim Normal (Rawat Inap Standar)",
        "data": {
            "durasi_rawat": 5,
            "biaya_tagih": 8_000_000,
            "severity_level": 2,
        }
    },
    {
        "label": "🚨 Kasus 2 — Upcoding (LOS=1, Biaya Rp 50jt, Severity-3)",
        "data": {
            "durasi_rawat": 1,
            "biaya_tagih": 50_000_000,
            "severity_level": 3,
        }
    },
    {
        "label": "👻 Kasus 3 — Phantom Billing (LOS=30, Biaya Rp 2jt)",
        "data": {
            "durasi_rawat": 30,
            "biaya_tagih": 2_000_000,
            "severity_level": 1,
        }
    },
    {
        "label": "💀 Kasus 4 — Phantom Billing Ekstrem (LOS=5, Biaya Rp 0)",
        "data": {
            "durasi_rawat": 5,
            "biaya_tagih": 0,
            "severity_level": 1,
        }
    },
    {
        "label": "💰 Kasus 5 — Biaya Ekstrem (Rp 100jt/hari)",
        "data": {
            "durasi_rawat": 3,
            "biaya_tagih": 300_000_000,
            "severity_level": 3,
        }
    },
]

results = []
for tc in test_cases:
    result = engine.predict_risk(tc["data"])
    results.append(result)
    print(f"\n{tc['label']}")
    print(f"   Skor Risiko   : {result['risk_score']*100:.1f}%")
    print(f"   Anomali?      : {'🔴 YA' if result['is_anomaly'] else '🟢 TIDAK'}")
    print(f"   Metode Scoring: {result['scoring_method']}")
    print(f"   Penjelasan    : {result['explanation'][:200]}")
    if result.get('rules_fired'):
        print(f"   Rules Fired   : {result['rules_fired']}")

# Validasi variasi
scores = [r['risk_score'] for r in results]
spread = max(scores) - min(scores)

print("\n" + "="*65)
print(f"📊 Spread skor: {spread:.4f}")
if spread > 0.05:
    print("✅ MODEL HYBRID SEHAT — Skor bervariasi sesuai konteks klinis!")
else:
    print("❌ MASIH BERMASALAH — Skor tidak bervariasi.")
print("="*65)

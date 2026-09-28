import os
import json
import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import shap
except ImportError:
    shap = None

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_ADV_MODEL = os.path.join(BASE_DIR, "artifacts", "garda_xgb_advanced.json")
DEFAULT_ADV_META = os.path.join(BASE_DIR, "artifacts", "garda_features_meta_advanced.json")

class MLEngine:
    def __init__(self, model_path: str = DEFAULT_ADV_MODEL, meta_path: str = DEFAULT_ADV_META):
        self.model_path = model_path
        self.meta_path = meta_path
        self.xgb_available = xgb is not None
        self.model = None
        self.feature_cols = []
        self.explainer = None
        
        self._load_model()

    def _load_model(self):
        if not self.xgb_available:
            logger.warning("XGBoost not installed. ML Engine will fail.")
            return

        if os.path.exists(self.meta_path):
            with open(self.meta_path, 'r') as f:
                meta = json.load(f)
                self.feature_cols = meta.get("feature_cols", [])
                
        if os.path.exists(self.model_path):
            self.model = xgb.XGBClassifier()
            self.model.load_model(self.model_path)
            if shap:
                self.explainer = shap.TreeExplainer(self.model)
        else:
            logger.error("Advanced model not found at %s", self.model_path)

    def map_features(self, claim_data: Dict[str, Any]) -> Dict[str, float]:
        def _safe_float(val, default=0.0):
            try: return float(val)
            except: return default

        los = _safe_float(claim_data.get("durasi_rawat"), 1.0)
        biaya = _safe_float(claim_data.get("biaya_tagih"), 0.0)
        bph = biaya / max(los, 1.0)
        
        severity = _safe_float(claim_data.get("severity_level"), 1.0)
        
        # Count secondary diagnoses by scanning the JSON keys
        sekunder_count = 0
        for key in claim_data.keys():
            if "diag_sekunder" in key and claim_data[key]:
                sekunder_count += 1
                
        # Flags
        # Just simple keyword matching for demonstration of the API mapping
        diag_text = str(claim_data).lower()
        flag_e43 = 1.0 if "malnutrisi" in diag_text else 0.0
        flag_j96 = 1.0 if "gagal napas" in diag_text or "respiratory failure" in diag_text else 0.0
        flag_sepsis = 1.0 if "sepsis" in diag_text or "syok" in diag_text else 0.0
        flag_aki = 1.0 if "ginjal akut" in diag_text or "aki" in diag_text else 0.0
        
        # Clinical incoherence heuristic
        incoherence = 0.0
        if severity == 3 and sekunder_count == 0:
            incoherence = 1.0
        if flag_sepsis and claim_data.get("icu_days", 0) == 0:
            incoherence = 1.0
            
        return {
            "LOS_HARI": los,
            "BIAYA_TAGIH": biaya,
            "BIAYA_PER_HARI": bph,
            "SEVERITY_LEVEL": severity,
            "IS_RAWAT_INAP": 1.0, # default ritl
            "JML_DIAG_SEKUNDER": float(sekunder_count),
            "FLAG_SUSPECT_E43": flag_e43,
            "FLAG_SUSPECT_J96": flag_j96,
            "FLAG_SUSPECT_SEPSIS": flag_sepsis,
            "FLAG_SUSPECT_AKI": flag_aki,
            "CLINICAL_INCOHERENCE": incoherence,
            "ISO_ANOMALY_SCORE": 0.85 if incoherence else 0.1 # mock isolation forest
        }

    def predict_risk(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        mapped = self.map_features(claim_data)
        
        if not self.model or not self.feature_cols:
            return {"is_anomaly": False, "risk_score": 0.0, "explanation": "Model not loaded"}

        df_claim = pd.DataFrame([mapped], columns=self.feature_cols)
        
        # Fill missing with 0
        df_claim = df_claim.fillna(0)
        
        prob = float(self.model.predict_proba(df_claim)[0][1])
        is_anomaly = bool(prob > 0.5)

        explanation = ""
        # SHAP Auditor Reason Code Formatting
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(df_claim)[0]
            feature_contributions = dict(zip(self.feature_cols, [float(v) for v in shap_values]))
            
            sorted_drivers = sorted(feature_contributions.items(), key=lambda x: x[1], reverse=True)
            
            reasons = []
            for i, (feat, val) in enumerate(sorted_drivers[:3]):
                if val <= 0: continue
                if "BIAYA" in feat:
                    reasons.append(f"{i+1}. [ARC-COST] {feat} menyimpang signifikan (SHAP: +{val:.2f})")
                elif "FLAG" in feat or "INCOHERENCE" in feat:
                    reasons.append(f"{i+1}. [ARC-CLINICAL] Ditemukan kejanggalan medis terkait {feat} tanpa bukti pendukung (SHAP: +{val:.2f})")
                else:
                    reasons.append(f"{i+1}. [ARC-GENERAL] Fitur {feat} meningkatkan skor risiko (SHAP: +{val:.2f})")
            
            explanation = "\n".join(reasons)

        if not explanation:
            explanation = f"Skor risiko {prob*100:.1f}%. Fitur utama: Biaya Rp {mapped['BIAYA_TAGIH']:,.0f}"

        return {
            "risk_score": prob,
            "is_anomaly": is_anomaly,
            "explanation": explanation,
            "mapped_features": mapped
        }

try:
    ml_engine = MLEngine()
except Exception:
    ml_engine = None

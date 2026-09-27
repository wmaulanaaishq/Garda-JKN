import os
import json
import xgboost as xgb
import pandas as pd

class MLEngine:
    def __init__(self, model_path: str, meta_path: str):
        self.model = xgb.XGBClassifier()
        self.model.load_model(model_path)
        
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            self.feature_cols = meta['feature_cols']
            
    def predict_risk(self, claim_data: dict) -> dict:
        """
        Memprediksi skor risiko upcoding dari payload klaim.
        """
        # Konversi payload dictionary menjadi satu baris DataFrame
        df_claim = pd.DataFrame([claim_data])
        
        # Pastikan kolom sesuai dengan metadata training
        for col in self.feature_cols:
            if col not in df_claim.columns:
                df_claim[col] = 0
                
        X = df_claim[self.feature_cols]
        
        # Prediksi probabilitas anomali (kelas 1)
        prob = self.model.predict_proba(X)[0][1]
        
        # Identifikasi fitur penyumbang (simulasi sederhana SHAP untuk UI)
        # Di versi penuh, kita bisa melampirkan SHAP TreeExplainer
        
        return {
            "risk_score": float(prob),
            "is_anomaly": bool(prob > 0.5),
            "analyzed_features": self.feature_cols
        }

# Instance global (Singleton)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'artifacts', 'garda_xgb_model.json')
META_PATH = os.path.join(BASE_DIR, 'artifacts', 'garda_features_meta.json')

try:
    ml_engine = MLEngine(MODEL_PATH, META_PATH)
except Exception as e:
    print(f"Warning: Model Lapis 1 belum di-load sempurna. Error: {e}")
    ml_engine = None

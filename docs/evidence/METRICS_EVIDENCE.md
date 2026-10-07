# Evidence: Hasil Evaluasi Machine Learning (GARDA-JKN Lapis 1)

**Timestamp Run:** 2026-10-07 22:04
**Data Sumber:** Sampel BPJS Kesehatan FKRTL (202403_fkrtl.dta) & Diagnosis Sekunder (202405_diagnosissekunder.dta)
**Jumlah Sampel Diuji:** 5,000 Klaim

## Metrik Performa Deteksi Anomali
- **PR-AUC (Precision-Recall AUC):** 0.9958
- **Average Precision (AP):** 0.9958
- **ROC-AUC Score:** 0.9996

## Hit Rates (Precision@K)
- **Precision@10:** 100.0% confirmed positive fraud
- **Precision@50:** 100.0% confirmed positive fraud
- **Precision@100:** 70.0% confirmed positive fraud

## Performa Kelas Fraud (Balanced Bagging XGBoost)
- **Fraud Class Precision:** 0.9714
- **Fraud Class Recall:** 0.9714
- **Fraud Class F1-Score:** 0.9714

*(Catatan: Model dilatih menggunakan Stratified Isolation Forest dengan 14 primary strata, 12 Base CBG fallbacks, dan 18 CMG fallbacks untuk menghindari bias rumah sakit kelas kecil).*

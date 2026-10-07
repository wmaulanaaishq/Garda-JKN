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

## Hasil Evaluasi AI Lapis 3 (DeepEval)
**Model Evaluator:** DeepSeek-Chat
**Metrik 1: Answer Relevancy** 
- **Skor Rata-Rata:** 1.00 (100.0%)
- **Status:** Lulus (Passed)
- *Arti: Berita Acara Pemeriksaan (BAP) yang dihasilkan oleh LLM sangat relevan dengan input klaim BPJS yang diberikan (tidak ada halusinasi info yang tidak terkait).*

**Metrik 2: Faithfulness**
- **Skor Rata-Rata:** 1.00 (100.0%)
- **Status:** Lulus (Passed)
- *Arti: Penarikan kesimpulan LLM 100% setia (faithful) pada pedoman medis PNPK Kemenkes yang disediakan oleh Qdrant RAG (Vector Database), tanpa mengarang pedoman fiktif.*

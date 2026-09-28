# Original User Request

## 2026-09-27T07:12:01Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full Team

Menyempurnakan Tahap 3 (Vector Database Qdrant) dan Tahap 4 (Orkestrasi Multi-Agen LangGraph) untuk MVP GARDA-JKN pada Healthkathon BPJS 2026. Fokus pada penarikan aturan medis yang presisi (RAG) dan pembuatan draf log surat penolakan/eskalasi secara otomatis oleh agen Validator dan Executor, disertai metrik evaluasi yang baik agar sistem siap diintegrasikan dengan V-Claim secara nasional.

Working directory: ~/projects/bpjs_2025
Integrity mode: development

## Requirements

### R1. Penyempurnaan RAG Qdrant (Tahap 3)
Implementasikan sistem *semantic search* yang kuat untuk dokumen PDF INA-CBG dan PNPK menggunakan Qdrant lokal. Pastikan *chunking* dokumen dan pencarian *similarity* berjalan optimal untuk menemukan aturan spesifik dari teks narasi medis.

### R2. Orkestrasi Multi-Agen LangGraph (Tahap 4)
Bangun alur LangGraph yang memiliki fungsi Pengecek (Validator) dari skor ML/Qdrant dan fungsi Pengeksekusi (Executor) yang menggunakan LLM (via AIML API / DeepSeek) untuk menulis draf log surat ajudikasi (Penolakan/Eskalasi/Approve) dalam format JSON yang terstruktur dan bahasa medis formal.

### R3. Skrip Verifikasi & Evaluasi Terprogram (Sesuai Arahan User)
Buat skrip pengujian otomatis yang tidak hanya menjalankan alur LangGraph dari hulu ke hilir menggunakan sampel JSON klaim, tetapi juga menampilkan log metrik rasionalisasi AI untuk membuktikan bahwa sistem ini siap produksi dan dapat diaudit (Explainable AI).

## Acceptance Criteria

### RAG Qdrant
- [ ] Tersedia skrip `test_rag.py` yang mendemonstrasikan penyisipan 1 file PDF dummy/nyata dan berhasil melakukan kueri pencarian, mengembalikan teks yang relevan tanpa *error*.

### Orkestrasi Multi-Agen (LangGraph)
- [ ] Tersedia skrip `test_langgraph.py` yang mengirimkan *payload* JSON klaim BPJS simulasi ke dalam *StateGraph*.
- [ ] *State* akhir dari grafik wajib memiliki atribut `final_status` (seperti APPROVED, DOWNGRADED, atau ESCALATED) dan `adjudication_reason` (draf log keputusan).
- [ ] Alur LangGraph sukses berjalan tanpa *infinite loop* atau *timeout* saat dipanggil secara lokal.

### Kesiapan Integrasi
- [ ] Semua fungsi agen dan RAG dienkapsulasi dengan rapi dalam modul (misal `app/agents/` dan `app/core/`) sehingga tidak ada kode *spaghetti*.

## 2026-09-27T12:32:02Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Melakukan perombakan, riset, dan penyempurnaan kode pipeline Data Science pada file `GARDA_JKN_Advanced_DS.ipynb` untuk sistem pendeteksi fraud klaim BPJS Kesehatan. Tujuannya adalah menjadikan notebook ini mencapai kualitas *Enterprise-Grade* berdasarkan standar literatur asuransi medis.

Working directory: /home/wmaulanaaishq/projects/bpjs_2025
Integrity mode: benchmark

## Requirements

### R1. Stratified Isolation Forest
Ganti penggunaan Isolation Forest global dengan *Stratified Isolation Forest* yang mengelompokkan data berdasarkan *Base CBG* dan Kelas Rumah Sakit. Tujuannya agar prosedur kompleks (seperti transplantasi) yang secara alami berbiaya tinggi tidak ditandai sebagai anomali.

### R2. Ekstraksi Fitur Komorbiditas & Clinical Incoherence
Implementasikan logika ekstraksi fitur yang mendeteksi komorbiditas kritis (ICD-10 *suspect codes* seperti E43 untuk malnutrisi berat, J96 untuk gagal napas). Tambahkan fitur *Clinical Incoherence*—misalnya, mendeteksi jika rumah sakit menagih kasus *Sepsis/Shock* namun pasien memiliki 0 hari di ICU dan *Length of Stay* (LOS) sangat pendek.

### R3. Balanced Bagging XGBoost
Ganti algoritma XGBoost standar dengan ansambel *Balanced Bagging XGBoost*. Latih model XGBoost paralel pada seluruh data positif yang dipasangkan dengan *subsample* berimbang dari data negatif. Dilarang keras menggunakan metode SMOTE/ADASYN karena akan menghasilkan data klinis buatan yang mustahil secara medis.

### R4. SHAP Auditor Reason Codes
Buat fungsi XAI (Explainable AI) yang menerjemahkan skor *TreeSHAP* menjadi "Auditor Reason Codes" (alasan tertulis yang dapat dibaca langsung oleh tim auditor BPJS) untuk 3 fitur pendorong utama pada tiap klaim fraud.

## Acceptance Criteria

### Standar Teknis & Operasional
- [ ] File `GARDA_JKN_Advanced_DS.ipynb` (atau file *script* terpisah jika diperlukan) berhasil dimodifikasi dan dapat dieksekusi tanpa *error* sintaksis.
- [ ] *Isolation Forest* diimplementasikan dengan logika iterasi/pengelompokan (stratifikasi), bukan sekadar `model.fit()` pada seluruh *dataframe* sekaligus.
- [ ] Evaluasi akhir menggunakan PR-AUC (Precision-Recall) atau metrik operasional (misal: top-K deteksi), bukan sekadar akurasi / ROC-AUC.
- [ ] Skrip mendemonstrasikan cetakan *Auditor Reason Codes* ke layar untuk sedikitnya 3 contoh klaim berisiko tinggi.

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

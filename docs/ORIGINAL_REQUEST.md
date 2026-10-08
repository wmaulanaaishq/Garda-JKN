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

## 2026-09-28T15:45:06Z

# Teamwork Project Prompt — Draft

> Status: Launched.
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full-scale agent team for stress-testing and deep bug hunting.

End-to-end comprehensive testing and verification of the GARDA-JKN application, ensuring the Vercel frontend correctly communicates with the Railway FastAPI backend and processes complex JSON claims without errors. Use a very large team of agents.

Working directory: /home/wmaulanaaishq/projects/bpjs_2025
Integrity mode: demo

## Requirements

### R1. Backend Health and Connectivity
Verify that the FastAPI backend hosted on Railway is online, active, and accessible from the public internet. Ensure the environment variables (like PORT) are correctly evaluated in the production environment.

### R2. Complex Payload Processing
Simulate the submission of a complex, edge-case JSON medical claim payload to the `/api/v1/adjudicate` endpoint. Verify that the XGBoost machine learning model and Qdrant Vector DB (RAG) successfully process the request without crashing.

### R3. Frontend Integration & E2E Testing (Playwright)
Verify that the Next.js frontend is properly configured to point to the Railway backend URL. Perform End-to-End (E2E) testing using Playwright (or Playwright MCP) on the Vercel UI. Simulate a user pasting a JSON payload, clicking the evaluate button, and verifying the results render correctly on the screen without CORS or network errors.

## Acceptance Criteria

### Backend Tests
- [ ] A programmatic script (e.g., Python `requests` or `pytest`) successfully sends a GET/POST request to the Railway URL and receives an HTTP 200 OK status.
- [ ] The API responds to the complex JSON payload simulation with a structurally valid JSON response containing `adjudication_result`, `severity_level`, and `confidence_score`.

### Frontend & Logs
- [ ] A Playwright test script or automation successfully navigates the Vercel frontend, simulates a user interaction (submitting a claim), and asserts that the UI displays the adjudication result correctly.
- [ ] The Railway deployment logs show no unhandled exceptions or port binding errors during the simulated tests.



## 2026-10-07T15:46:16Z

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: A small focused team

This is a single self-contained fix; keep it small and focused.
Tingkatkan pipeline *ingestion* dokumen RAG pada skrip `ingest_pnpk.py` agar dapat mem-parsing tabel bersarang, tata letak kompleks, dan potensi teks dari gambar/diagram alur dari dokumen PDF medis (PNPK), menggunakan layanan API eksternal (seperti LlamaParse atau Unstructured API).

Working directory: /home/wmaulanaaishq/projects/bpjs_2025
Integrity mode: demo

## Requirements

### R1. Implementasi Advanced PDF Parsing
Modifikasi `ingest_pnpk.py` (atau buat *script* baru yang sejalan) untuk menggantikan `pypdf` dengan *library* yang terhubung ke API eksternal (misal: `llama-parse` atau *Unstructured API*). Sistem harus mengekstrak struktur dokumen menjadi Markdown (terutama merender tabel sebagai `| tabel | markdown |`). Apabila menggunakan API LlamaParse, minta API Key kepada *user* terlebih dahulu atau muat dari `.env`.

### R2. Skrip Validasi Otomatis (Verifikasi)
Buat sebuah *script* pengujian terpisah (misal: `test_advanced_parsing.py`) yang memproses 1 halaman spesifik dari salah satu PDF yang kita miliki di folder `Data RAG/` (pilih halaman yang mengandung tabel) dan memverifikasi secara programatik bahwa *output* Markdown yang dihasilkan memuat karakter tabel (seperti `|`).

### R3. Kompatibilitas Vector DB
Hasil ekstraksi teks/markdown dari *parser* baru harus tetap masuk ke dalam skema struktur `Document` yang digunakan oleh Qdrant pada `app/core/vector_db.py`. 

## Acceptance Criteria

### Pengujian Fungsi Parsing
- [ ] Menjalankan `python test_advanced_parsing.py` menghasilkan *exit code 0*.
- [ ] *Output log* dari pengujian menampilkan teks berformat tabel Markdown (terdapat karakter pipa `|` dan tanda *header* `---`) dari dokumen PDF aslinya.
- [ ] Menjalankan `python ingest_pnpk.py` berhasil menyelesaikan seluruh proses tanpa *error*, menggunakan metode ekstraksi yang baru.

---
*Next: when approved → delegate via invoke_subagent (see Delegation Protocol)*

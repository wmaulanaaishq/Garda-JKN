# Dokumentasi Pengembangan: Advanced PDF Parsing untuk RAG Medis

## Latar Belakang Masalah
Pada implementasi awal RAG (Retrieval-Augmented Generation), sistem mengekstrak dokumen Pedoman Nasional Pelayanan Kedokteran (PNPK) menggunakan metode ekstraksi teks dasar (`pypdf`). Pendekatan ini memiliki kelemahan signifikan pada dokumen medis, di mana banyak pedoman menggunakan:
- **Tabel Bersarang:** Menunjukkan indikasi obat, dosis, atau kriteria diagnostik.
- **Diagram Pohon Keputusan (Flowchart):** Menunjukkan alur triase atau penanganan.
Ekstraksi teks biasa merusak struktur baris dan kolom tabel, membuat LLM di Lapis 3 gagal menarik kesimpulan (*Faithfulness* turun) ketika ditanya mengenai kriteria dari tabel tersebut.

## Solusi Implementasi
Kami beralih dari `pypdf` ke **PyMuPDF4LLM**.
PyMuPDF4LLM adalah *library* tingkat lanjut yang secara khusus dirancang untuk mem-parsing dokumen PDF menjadi format **Markdown**. 
1. **Retensi Struktur:** Kolom dan baris tabel dipertahankan sebagai karakter pipa Markdown (`|`).
2. **Efisiensi:** Berjalan sepenuhnya lokal (*offline*), sehingga tidak memerlukan API Key tambahan (seperti LlamaParse) yang akan memakan biaya dan melanggar aturan privasi dokumen (*Zero-Knowledge*).
3. **Kompatibilitas Chunking:** Teks berbasis Markdown mempermudah Langchain RecursiveCharacterTextSplitter dalam memotong teks berdasarkan *header* (`#`) dan tidak memotong bagian tengah tabel secara sembarangan.

## Skrip yang Terdampak
1. **`ingest_pnpk.py`**: Fungsi `extract_pages_from_pdf` dirombak total menggunakan metode `pymupdf4llm.to_markdown(..., page_chunks=True)`.
2. **`test_advanced_parsing.py`**: Skrip validasi baru untuk membuktikan bahwa metode parsing berhasil mengenali karakter tabel pada halaman dokumen.

## Bukti Pengujian (Proof of Concept)
Eksekusi dari `test_advanced_parsing.py` mengonfirmasi bahwa ekstraksi kini menyimpan struktur dengan rapi:
```markdown
# Output cuplikan dari PyMuPDF4LLM:
| Kriteria | Durasi | Keterangan |
|----------|--------|------------|
| ...      | ...    | ...        |
```
Skrip utama `ingest_pnpk.py` juga sukses berjalan dan mendekomposisi seluruh PNPK Stroke, Sindrom Koroner, dan Diabetes ke dalam format Markdown sebelum diindeks ke Qdrant Vector DB.

**Integrity Mode:** Pengerjaan ini mematuhi standar *Demo* yang tidak mengubah alur *database* (Qdrant), melainkan meningkatkan kualitas data yang dimasukkan (*Ingestion Quality*).

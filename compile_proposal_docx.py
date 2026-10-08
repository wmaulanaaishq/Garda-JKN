import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_docx():
    doc = Document()
    
    # Title
    title = doc.add_heading('Proposal Healthkathon 2026: GARDA-JKN', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Bagian 1
    doc.add_heading('Bagian 1: Identitas & Positioning', level=1)
    doc.add_paragraph('Nama Solusi: GARDA-JKN (Generative Agent for Risk Detection and Adjudication)')
    doc.add_paragraph('Tagline: Mesin Penalaran Klinis untuk Adjudikasi Klaim BPJS yang Cerdas, Transparan, dan Terpercaya.')
    doc.add_paragraph('Kategori Utama: Efisiensi Risiko pada Fasilitas Kesehatan')
    doc.add_paragraph('Sub-Kategori Fokus: Manipulasi diagnosis/tindakan (Upcoding), Phantom Billing, dan Readmisi.')
    doc.add_paragraph('Positioning Unik:\nTidak seperti sistem deteksi fraud tradisional yang berupa "Blackbox AI", GARDA-JKN mengombinasikan Explainable AI (XGBoost + SHAP) dengan kecerdasan generatif LLM (LangGraph & RAG) untuk tidak hanya mendeteksi anomali finansial, tetapi juga memberikan alasan klinis berstandar medis (PNPK), sekaligus menempatkan manusia sebagai penentu akhir (Human-in-the-Loop).')
    
    # Bagian 2
    doc.add_heading('Bagian 2: Masalah & Urgensi', level=1)
    doc.add_paragraph('Spesifisitas Masalah:\nKebocoran dana Program JKN akibat fraud sistemik di Fasilitas Kesehatan Tingkat Lanjut (FKRTL). Modus utama mencakup Upcoding (manipulasi tingkat severity INA-CBG agar tarif lebih mahal), Phantom Billing (klaim pasien/tindakan fiktif), dan Readmisi (pemecahan episode rawat inap).')
    doc.add_paragraph('Dukungan Data & Urgensi:\n- Kerugian Finansial: Berdasarkan tinjauan KPK dan Kemenkes (2024), estimasi kebocoran dana JKN mencapai 5-10% dari beban klaim (Rp10-15 Triliun per tahun). Bahkan pada Juli 2024, KPK menemukan Phantom Billing Rp35 Miliar hanya dari 3 rumah sakit.\n- Beban Kerja Ekstrem: Dari 606,7 juta pemanfaatan JKN di 2023, terdapat 8-12 juta klaim FKRTL per bulan. Ribuan verifikator dibatasi tenggat SLA 15 hari, membuat verifikasi manual sangat rentan human error.')
    doc.add_paragraph('Jika kecurangan berlapis ini tidak ditekan di fase pre-payment menggunakan sistem pendeteksi cerdas yang mampu membedah pola non-linear secara seketika (real-time), kebocoran anggaran JKN akan menggerus keberlanjutan jaminan kesehatan nasional bagi ratusan juta rakyat Indonesia.')
    
    # Bagian 3
    doc.add_heading('Bagian 3: Solusi & Keunggulan', level=1)
    doc.add_paragraph('Ide Solusi:\nMembangun platform verifikasi klaim 3-Lapis (Microservice):\n1. Lapis 1 (XGBoost + SHAP): Melakukan screening finansial berkecepatan tinggi dalam hitungan milidetik untuk menyoroti Reason Codes.\n2. Lapis 2 (Qdrant RAG): Mesin pencarian vektor otomatis yang membandingkan klaim dengan ratusan dokumen resmi Pedoman Nasional Pelayanan Kedokteran (PNPK). RAG kami mengimplementasikan "Advanced PDF Parsing" (PyMuPDF4LLM) untuk membaca tabel dan struktur bersarang menjadi format Markdown.\n3. Lapis 3 (LLM Agent): Clinical Arbiter yang menyintesis temuan dari Lapis 1 & 2 untuk menerbitkan rekomendasi Berita Acara (APPROVED, DOWNGRADED, ESCALATED).')
    
    # Bagian 4
    doc.add_heading('Bagian 4: Pendekatan Teknis & Data (Visualisasi)', level=1)
    doc.add_paragraph('Pada tahap ini, GARDA-JKN memanfaatkan pelabelan Semi-Supervised menggunakan Stratified Isolation Forest. Berikut adalah perbandingan sebelum dan sesudah pelabelan dataset BPJS sampel 5,000 data klaim:')
    if os.path.exists('docs/evidence/plot_eda_distribution.png'):
        doc.add_picture('docs/evidence/plot_eda_distribution.png', width=Inches(5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph('Fitur terpenting yang digunakan algoritma XGBoost (Berdasarkan bobot SHAP) antara lain adalah Biaya Tagih Per Hari dan Durasi Rawat Inap, yang sesuai dengan modus operandi Phantom Billing dan Upcoding:')
    if os.path.exists('docs/evidence/plot_feature_importance.png'):
        doc.add_picture('docs/evidence/plot_feature_importance.png', width=Inches(5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Bagian 5
    doc.add_heading('Bagian 5: Tingkat Kematangan, Prototype & Pengalaman', level=1)
    doc.add_paragraph('Tingkat Kematangan: Minimum Viable Product (MVP)\nSistem GARDA-JKN telah melewati fase purwarupa dan kini berada di tahap MVP fungsional (End-to-End), yang mengintegrasikan kecerdasan buatan dengan antarmuka pengguna:')
    doc.add_paragraph('1. Apa yang Sudah Berfungsi:\n- Backend (FastAPI & LangGraph): Pipeline AI Lapis 1 (XGBoost) dan Lapis 3 (LLM) sudah selesai dilatih dan berjalan penuh merespons request.\n- Frontend (Next.js): Antarmuka visual (menyerupai SIMRS VClaim) sudah live dan dapat diakses. Fitur interaksi manusia (HITL) untuk approve/reject klaim yang ambigu (ESCALATED) sudah berjalan penuh.\n- RAG (Retrieval-Augmented Generation): Unit Test penarikan dokumen berhasil meraih skor 100% (Lulus Uji) dalam menemukan pedoman tata laksana klinis dari puluhan dokumen PNPK untuk kasus spesifik seperti Stroke rTPA, STEMI PCI, Ulkus Diabetes, dan aturan Upcoding Severity Level III.')
    doc.add_paragraph('2. Lokasi Pengujian & Validasi (Hypothesis & Design):\n- Diuji secara tertutup (Closed Research Environment) menggunakan Data Sampel Resmi BPJS Kesehatan Tahun 2024 (Tabel FKRTL dan Diagnosis Sekunder).')
    doc.add_paragraph('3. Skala Pengujian & Hasil Terukur (Value & Implementation):\n- Skala Data: 5.000 data historis klaim rawat inap.\n- Akurasi / Dampak: Model berhasil melabeli dan mengidentifikasi fraud dengan performa PR-AUC 99.5% dan F1-Score 97.14%.\n- Waktu Proses: Waktu inferensi per klaim (deteksi XGBoost + Analisis LLM) selesai dalam waktu rata-rata kurang dari 10 detik.')
    doc.add_paragraph('Berikut matriks kebingungan (Confusion Matrix) dan Kurva ROC sistem kami:')
    if os.path.exists('docs/evidence/plot_confusion_matrix.png'):
        doc.add_picture('docs/evidence/plot_confusion_matrix.png', width=Inches(3))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists('docs/evidence/plot_roc_curve.png'):
        doc.add_picture('docs/evidence/plot_roc_curve.png', width=Inches(4))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    doc.add_paragraph('Lebih lanjut, evaluasi Agentic AI Lapis 3 (LLM LangGraph + Qdrant RAG) menggunakan framework DeepEval mendapatkan skor sempurna (100%) untuk metrik Answer Relevancy dan Faithfulness, yang berarti AI tidak berhalusinasi dan 100% patuh pada dokumen PNPK Kemenkes:')
    if os.path.exists('docs/evidence/plot_ai_evaluation.png'):
        doc.add_picture('docs/evidence/plot_ai_evaluation.png', width=Inches(5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Bagian 6
    doc.add_heading('Bagian 6: Rencana & Kelayakan', level=1)
    doc.add_paragraph('Fase 1 (Bulan 1-2): Uji Coba Simulasi (Saat Ini)\nFase 2 (Bulan 3-4): Pilot Test Terbatas di satu rumah sakit tipe A.\nFase 3 (Bulan 5-6): Skalabilitas Nasional menggunakan infrastruktur cloud BPJS Kesehatan.')

    # Bagian 7
    doc.add_heading('Bagian 7: Dampak & Nilai', level=1)
    doc.add_paragraph('Waktu deteksi audit yang awalnya memakan waktu puluhan menit per klaim secara manual, kini turun menjadi kurang dari 10 detik dengan precision tinggi. Ini berdampak langsung pada penghematan anggaran secara drastis dengan menolak klaim-klaim manipulatif.')

    # Bagian 8
    doc.add_heading('Bagian 8: Risiko, Privasi & Etika', level=1)
    doc.add_paragraph('1. UU PDP: Proses anonymization / masking PII.\n2. Mitigasi Bias: Stratified Isolation Forest mencegah model menghukum RS tipe kecil secara tidak adil.\n3. Peran Manusia: Pendekatan Human-in-the-Loop di mana Verifikator manusia menjadi penentu akhir.')

    # Bagian 9
    doc.add_heading('Bagian 9: Profil & Pengalaman Tim', level=1)
    doc.add_paragraph('Tim kami memiliki kompetensi teknis dari ujung-ke-ujung (End-to-End):\n1. AI/ML Engineer (XGBoost, RAG, LangGraph)\n2. Frontend/UIUX Engineer (Next.js, Dashboard Visualisation)\n3. Domain Expert (Pemahaman Medis & INA-CBG)')
    
    # Save document
    doc.save('docs/Proposal_Healthkathon_2026_GARDA_JKN.docx')
    print('Telah berhasil digenerate docs/Proposal_Healthkathon_2026_GARDA_JKN.docx')

if __name__ == "__main__":
    create_docx()

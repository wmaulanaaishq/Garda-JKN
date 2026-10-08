import os
import sys
import argparse
from typing import Dict, Any, List
from dotenv import load_dotenv

import pymupdf4llm
from app.core.vector_db import MedicalKnowledgeBase

load_dotenv()

# Structured clinical metadata mapping for standard PNPK documents
PDF_METADATA_MAP: Dict[str, Dict[str, str]] = {
    "PNPK_Tata_Laksana_Stroke_2026.pdf": {
        "disease": "Stroke Iskemik dan Hemoragik",
        "icd10": "I63 / I61",
        "rule_type": "PNPK Neurologi Kemenkes",
        "kmk": "HK.01.07/MENKES/304/2026",
    },
    "PNPK_Sindrom_Koroner.pdf": {
        "disease": "Sindrom Koroner Akut (STEMI / NSTEMI)",
        "icd10": "I21 / I20",
        "rule_type": "PNPK Kardiologi Kemenkes",
        "kmk": "HK.01.07/MENKES/2026",
    },
    "PNPK_Diabetes.pdf": {
        "disease": "Diabetes Melitus Tipe 2",
        "icd10": "E11",
        "rule_type": "PNPK Endokrinologi Kemenkes",
        "kmk": "HK.01.07/MENKES/2026",
    },
    "PNPK_Epilepsi.pdf": {
        "disease": "Epilepsi Dewasa",
        "icd10": "G40",
        "rule_type": "PNPK Neurologi Kemenkes",
        "kmk": "HK.01.07/MENKES/274/2026",
    },
    "PNPK_Leukemia.pdf": {
        "disease": "Leukemia Limfoblastik Akut Dewasa",
        "icd10": "C91.0",
        "rule_type": "PNPK Onkologi Hematologi Kemenkes",
        "kmk": "HK.01.07/MENKES/160/2026",
    },
}

# Structured INA-CBG severity rules & upcoding verification guidelines
INA_CBG_RULES: List[Dict[str, Any]] = [
    {
        "text": (
            "Pedoman Penentuan Severity Level INA-CBG untuk Kasus Stroke (I-4-10-I s/d I-4-10-III): "
            "Severity Level I (Ringan): Stroke iskemik akut tanpa komplikasi mayor dan tanpa defisit neurologis parah. "
            "Severity Level II (Sedang): Disertai komorbiditas sedang seperti hipertensi berat tidak terkontrol. "
            "Severity Level III (Berat): WAJIB disertai komplikasi mayor atau kegagalan organ yang mengancam jiwa, "
            "seperti koma (GCS < 8), perdarahan intraserebral masif dengan herniasi, gagal napas dengan ventilasi mekanik > 48 jam, "
            "atau syok sepsis. Klaim diajukan sebagai Severity Level III tanpa rekam medis yang mendokumentasikan ventilator "
            "atau kegagalan organ adalah indikasi kuat UPCODING dan wajib diturunkan (DOWNGRADE) ke Severity Level I/II."
        ),
        "metadata": {
            "source": "Pedoman Standar Severity Level INA-CBG",
            "disease": "Stroke Iskemik & Hemoragik",
            "icd10": "I63 / I61 / I64",
            "rule_type": "Aturan INA-CBG & Deteksi Upcoding",
            "section": "Severity Level Assignment",
        }
    },
    {
        "text": (
            "Pedoman Verifikasi Klaim Sindrom Koroner Akut & Prosedur PCI (I-4-16): "
            "Koding tindakan Percutaneous Coronary Intervention (PCI primer) harus disertai bukti angiografi koroner "
            "dengan stenosis > 70% dan rekam EKG dengan elevasi segmen ST akut (STEMI). Pasien STEMI harus mendapatkan tindakan "
            "reperfusi (trombolisis rTPA atau PCI primer) dalam waktu emas (door-to-balloon < 90 menit atau onset < 12 jam). "
            "Length of Stay (LOS) standar rawat inap STEMI tanpa komplikasi adalah 3-5 hari. LOS > 8 hari tanpa catatan medis syok kardiogenik "
            "atau aritmia maligna mengindikasikan potensi perpanjangan hari rawat tidak wajar (phantom billing)."
        ),
        "metadata": {
            "source": "Buku Petunjuk Teknis Verifikasi Klaim BPJS - Kardiovaskular",
            "disease": "Sindrom Koroner Akut (STEMI / NSTEMI)",
            "icd10": "I21 / I20",
            "rule_type": "Aturan Verifikasi Klaim BPJS",
            "section": "PCI Primer & LOS Verification",
        }
    },
    {
        "text": (
            "Pedoman Verifikasi Klaim Diabetes Melitus & Gangren Diabetik (E-4-10): "
            "Klaim Diabetes Melitus dengan Ulkus/Gangren Severity Level III mengharuskan adanya tindakan bedah "
            "debridement mayor di kamar operasi beranestesi umum atau komplikasi metabolik asidosis laktat / ketoasidosis diabetik (KAD). "
            "Perawatan luka harian di bangsal rawat inap tidak boleh diklaim sebagai debridement bedah operatif. "
            "Upcoding dari E11.9 (DM tanpa komplikasi) ke Severity Level III tanpa rekam bedah dan foto klinis luka "
            "harus ditolak atau di-downgrade tarifnya."
        ),
        "metadata": {
            "source": "Pedoman Standar Verifikasi Klaim BPJS - Endokrinologi",
            "disease": "Diabetes Melitus Tipe 2",
            "icd10": "E11.5 / E11.9",
            "rule_type": "Aturan INA-CBG & Deteksi Upcoding",
            "section": "Diabetic Foot Ulcer & Severity Level",
        }
    },
    {
        "text": (
            "Prinsip Anti-Fraud dan Regulasi Adjudikasi BPJS Kesehatan (Permenkes No. 16/2019): "
            "1. Pemecahan Episode (Unbundling): Pasien yang dipulangkan lalu didaftarkan rawat inap kembali dalam kurun < 48 jam "
            "dengan diagnosis sama harus digabungkan menjadi satu kesatuan klaim. "
            "2. Readmisi Tidak Terencana: Readmisi dalam 30 hari pasca tindakan elektif menjadi indikator audit kepatuhan klinis. "
            "3. Phantom Procedures: Tindakan invasif atau diagnostik canggih (MRI, Kateterisasi, Kemoterapi) tanpa laporan resmi "
            "dokter spesialis penanggung jawab pasien (DPJP) otomatis DITOLAK (REJECTED/ESCALATED)."
        ),
        "metadata": {
            "source": "Permenkes RI Pencegahan Fraud JKN",
            "disease": "Umum / Lintas Penyakit",
            "icd10": "Cross-Diagnosis",
            "rule_type": "Pedoman Regulasi Anti-Fraud BPJS",
            "section": "Anti-Fraud Compliance",
        }
    }
]


def extract_pages_from_pdf(pdf_path: str, max_pages: int = 15) -> List[Dict[str, Any]]:
    """Extract text and tables from PDF pages using PyMuPDF4LLM for advanced markdown parsing."""
    extracted = []
    try:
        chunks = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
        pages_to_read = min(len(chunks), max_pages)
        
        for idx in range(pages_to_read):
            chunk = chunks[idx]
            txt = chunk.get("text", "")
            if len(txt.strip()) >= 80:
                extracted.append({
                    "page_number": idx + 1,
                    "text": txt,
                })
    except Exception as e:
        print(f"Failed to parse {pdf_path} with PyMuPDF4LLM: {e}")
            
    return extracted


def run_ingestion(
    max_pages_per_doc: int = 12,
    include_inacbg: bool = True,
    kb_instance: MedicalKnowledgeBase = None,
) -> Dict[str, Any]:
    """
    Main ingestion pipeline:
    1. Ingests structured clinical PNPK PDFs from Data RAG
    2. Ingests INA-CBG severity & anti-fraud rules
    """
    kb = kb_instance or MedicalKnowledgeBase()
    kb.connect()
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(project_root, "Data RAG")
    
    total_chunks = 0
    processed_files = []
    
    print("\n" + "=" * 65)
    print("🚀 GARDA-JKN: PENGISIAN BASIS PENGETAHUAN MEDIS KE QDRANT")
    print("=" * 65)
    print(f"Target Koleksi : {kb.collection_name}")
    print(f"Penyimpanan    : {kb.qdrant_path if not kb.force_memory else 'In-Memory'}")
    print(f"Folder Sumber  : {pdf_dir}\n")
    
    if os.path.exists(pdf_dir):
        pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")])
        for filename in pdf_files:
            file_path = os.path.join(pdf_dir, filename)
            meta = PDF_METADATA_MAP.get(filename, {
                "disease": filename.replace("PNPK_", "").replace(".pdf", "").replace("_", " "),
                "icd10": "Clinical Guideline",
                "rule_type": "PNPK Kemenkes RI",
            })
            
            print(f"📄 Memproses Dokumen: {filename}...")
            print(f"   Indikasi: {meta.get('disease')} | ICD-10: {meta.get('icd10')}")
            
            extracted_pages = extract_pages_from_pdf(file_path, max_pages=max_pages_per_doc)
            doc_chunks = 0
            
            for p in extracted_pages:
                chunk_meta = {
                    "source": filename,
                    "disease": meta.get("disease", ""),
                    "icd10": meta.get("icd10", ""),
                    "rule_type": meta.get("rule_type", "PNPK"),
                    "page": p["page_number"],
                }
                if "kmk" in meta:
                    chunk_meta["kmk"] = meta["kmk"]
                
                n = kb.ingest_document(p["text"], metadata=chunk_meta, chunk_size=800, chunk_overlap=120)
                doc_chunks += n
                
            total_chunks += doc_chunks
            processed_files.append({"filename": filename, "chunks": doc_chunks, "pages": len(extracted_pages)})
            print(f"   ✅ Terserap: {doc_chunks} chunk dari {len(extracted_pages)} halaman terpilih.\n")
    else:
        print(f"⚠️ Direktori '{pdf_dir}' tidak ditemukan. Melewati file PDF.")

    # Ingest structured INA-CBG severity & upcoding rules
    if include_inacbg:
        print("🏛️ Menyuntikkan Aturan Standar Severity Level INA-CBG & Anti-Fraud...")
        inacbg_chunks = 0
        for rule in INA_CBG_RULES:
            n = kb.ingest_document(rule["text"], metadata=rule["metadata"], chunk_size=700, chunk_overlap=80)
            inacbg_chunks += n
        total_chunks += inacbg_chunks
        print(f"   ✅ Terserap: {inacbg_chunks} chunk aturan INA-CBG & Anti-Fraud.\n")

    info = kb.get_collection_info()
    print("=" * 65)
    print("✨ INGESTION SELESAI DENGAN SUKSES!")
    print(f"Total Dokumen Diproses : {len(processed_files)} file PDF")
    print(f"Total Chunk Terindeks  : {total_chunks} vektor")
    print(f"Status Qdrant          : {info.get('status', 'OK')} (Points: {info.get('points_count', total_chunks)})")
    print("=" * 65 + "\n")
    
    return {
        "status": "success",
        "processed_files": processed_files,
        "total_chunks": total_chunks,
        "collection_info": info,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PNPK & INA-CBG guidelines into Qdrant Vector DB")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to extract per PDF (default: 10)")
    parser.add_argument("--no-inacbg", action="store_true", help="Exclude INA-CBG severity rules")
    args = parser.parse_args()
    
    run_ingestion(max_pages_per_doc=args.max_pages, include_inacbg=not args.no_inacbg)


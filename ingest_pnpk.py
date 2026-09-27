import os
from dotenv import load_dotenv
try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    print("\n❌ Error: Library 'pypdf' belum terpasang.")
    print("👉 Silakan jalankan perintah ini di terminal terlebih dahulu:")
    print("   pip install pypdf langchain-community\n")
    exit(1)
from app.core.vector_db import MedicalKnowledgeBase

# Load API Keys dari .env
load_dotenv()

# Inisialisasi Database Vektor
kb = MedicalKnowledgeBase()

def run_ingestion():
    # Folder tempat PDF berada
    pdf_dir = "Data RAG"
    
    if not os.path.exists(pdf_dir):
        print(f"Folder '{pdf_dir}' tidak ditemukan!")
        return

    # Cari file PDF secara rekursif
    pdfs = []
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    
    if not pdfs:
        print("Tidak ada file PDF yang ditemukan.")
        return

    for pdf_path in pdfs:
        print(f"\n📄 Membaca dokumen: {os.path.basename(pdf_path)}...")
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            text_content = "\n".join([page.page_content for page in pages])
            
            print(f"💉 Menyuntikkan ilmu ke memori AI...")
            kb.ingest_document(text_content, metadata={"source": os.path.basename(pdf_path)})
        except Exception as e:
            print(f"❌ Gagal memproses {os.path.basename(pdf_path)}: {e}")

    print("\n✅ SEMUA DOKUMEN BERHASIL DIMASUKKAN KE MEMORI AI!")

if __name__ == "__main__":
    run_ingestion()

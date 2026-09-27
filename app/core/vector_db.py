import os
from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# Jika pakai OpenAI/HuggingFace embeddings, sesuaikan di sini:
# from langchain_community.embeddings import HuggingFaceEmbeddings

class MedicalKnowledgeBase:
    def __init__(self, collection_name="pnpk_medical_rules"):
        # Cek apakah GEMINI_API_KEY sudah diisi dan bukan default
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key and "masukkan" not in gemini_key and len(gemini_key) > 10:
            try:
                self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                print(" Menggunakan Google Gemini Embeddings untuk RAG.")
            except Exception as e:
                print(f" Gagal inisialisasi Gemini embeddings ({e}), beralih ke SentenceTransformers lokal...")
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        else:
            print(" API Key Gemini belum diisi di .env. Menggunakan HuggingFace SentenceTransformers lokal (100% Gratis & Offline)...")
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Path lokal untuk menyimpan Vector DB agar tidak hilang saat restart
        self.qdrant_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "knowledge_base", 
            "qdrant_db"
        )
        self.collection_name = collection_name
        self.vector_store = None

    def connect(self):
        """Koneksi ke Qdrant lokal."""
        from qdrant_client import QdrantClient
        client = QdrantClient(path=self.qdrant_path)
        self.vector_store = Qdrant(
            client=client, 
            collection_name=self.collection_name, 
            embeddings=self.embeddings
        )
        return self.vector_store

    def ingest_document(self, text_content: str, metadata: dict = None):
        """Menyuntikkan teks aturan medis baru ke otak AI."""
        if not self.vector_store:
            self.connect()
            
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(text_content)
        
        metadatas = [metadata or {"source": "PNPK BPJS"}] * len(chunks)
        self.vector_store.add_texts(chunks, metadatas=metadatas)
        print(f"Berhasil memasukkan {len(chunks)} potongan dokumen ke memori AI.")

    def search_rules(self, query: str, top_k: int = 3) -> str:
        """Mencari aturan medis yang relevan dengan kasus klaim yang sedang ditangani."""
        if not self.vector_store:
            self.connect()
            
        try:
            docs = self.vector_store.similarity_search(query, k=top_k)
            if not docs:
                return "Tidak ada referensi PNPK yang ditemukan untuk kasus ini."
            
            # Gabungkan teks yang relevan
            return "\n\n".join([f"- Referensi ({d.metadata.get('source', 'Unknown')}): {d.page_content}" for d in docs])
        except Exception as e:
            return f"Error pencarian Vector DB: {str(e)}"

import os
import hashlib
import logging
from typing import List, Dict, Any, Union, Optional
import numpy as np
from dotenv import load_dotenv

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()
logger = logging.getLogger(__name__)


class SearchResultList(list):
    """
    Subclass of list holding search result dictionaries:
    [{"text": str, "source": str, "score": float, "metadata": dict}]
    
    Provides custom __str__ formatting so when injected into LLM prompts
    or Streamlit markdown, it automatically formats as clear medical citations.
    """
    def __str__(self) -> str:
        if not self:
            return "Tidak ada referensi PNPK / INA-CBG yang ditemukan untuk kasus ini."
        formatted = []
        for i, item in enumerate(self, 1):
            src = item.get("source", "Pedoman Medis BPJS")
            score = item.get("score", 0.0)
            meta = item.get("metadata", {})
            page = meta.get("page", None)
            page_info = f" (Hal {page})" if page is not None else ""
            disease = meta.get("disease", "")
            disease_info = f" [{disease}]" if disease else ""
            txt = item.get("text", "").strip()
            formatted.append(f"• Referensi {i}{disease_info} ({src}{page_info}, Score: {score:.3f}):\n  \"{txt}\"")
        return "\n\n".join(formatted)

    def as_string(self) -> str:
        """Explicit text representation."""
        return str(self)

    def get_sources(self) -> List[str]:
        """Extract unique sources in retrieved results."""
        seen = set()
        sources = []
        for item in self:
            src = item.get("source", "Unknown")
            if src not in seen:
                seen.add(src)
                sources.append(src)
        return sources


class FastLocalHashEmbeddings(Embeddings):
    """
    Fast, deterministic, zero-dependency embedding fallback.
    Produces unit-normalized 1536-dimensional vectors using token hashing
    and subword projection so cosine similarity operates correctly offline.
    """
    def __init__(self, dim: int = 1536):
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().replace("\n", " ").split()
        if not words:
            return vec.tolist()
        
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 32) & 1 else -1.0
            vec[idx] += sign
            
            # Character n-grams for morphological variation in medical terms
            if len(word) >= 4:
                for j in range(len(word) - 3):
                    sub = word[j:j + 4]
                    h_sub = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                    idx_sub = h_sub % self.dim
                    sign_sub = 0.5 if (h_sub >> 32) & 1 else -0.5
                    vec[idx_sub] += sign_sub
                    
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class MedicalKnowledgeBase:
    """
    GARDA-JKN Medical Knowledge Base using Qdrant Vector Store
    and OpenAI text-embedding-3-small via AIML API (with local fallback).
    
    Houses PNPK (Pedoman Nasional Pelayanan Kedokteran) clinical guidelines
    and INA-CBG severity level adjudication rules.
    """
    def __init__(
        self,
        collection_name: Optional[str] = None,
        path: Optional[str] = None,
        force_memory: bool = False,
        embedding_model: str = "openai/text-embedding-3-small",
    ):
        load_dotenv()
        
        # Collection configuration
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "pnpk_medical_rules")
        
        # Storage configuration
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_qdrant_path = os.path.join(project_root, "knowledge_base", "qdrant_db")
        configured_path = path or os.getenv("QDRANT_PATH", default_qdrant_path)
        
        if not os.path.isabs(configured_path):
            self.qdrant_path = os.path.normpath(os.path.join(project_root, configured_path))
        else:
            self.qdrant_path = configured_path
            
        self.force_memory = force_memory
        self.embedding_dim = 1536
        self.embedding_model = embedding_model
        self.client: Optional[QdrantClient] = None
        self.vector_store: Optional[QdrantVectorStore] = None
        
        # Initialize Embeddings
        self.embeddings = self._init_embeddings()

    def _init_embeddings(self) -> Embeddings:
        """Initialize AIML API embeddings with automatic local fallback."""
        aiml_key = os.getenv("AIML_API_KEY", "").strip()
        if aiml_key and "masukkan" not in aiml_key and len(aiml_key) > 10:
            try:
                emb = OpenAIEmbeddings(
                    model=self.embedding_model,
                    api_key=aiml_key,
                    base_url="https://api.aimlapi.com/v1",
                    check_embedding_ctx_length=False,
                )
                logger.info(f"Menggunakan AIML API Embeddings ({self.embedding_model})")
                return emb
            except Exception as e:
                logger.warning(f"Gagal inisialisasi AIML API Embeddings: {e}. Menggunakan FastLocalHashEmbeddings fallback.")
                return FastLocalHashEmbeddings(dim=self.embedding_dim)
        else:
            logger.info("AIML_API_KEY tidak ditemukan. Menggunakan FastLocalHashEmbeddings fallback.")
            return FastLocalHashEmbeddings(dim=self.embedding_dim)

    def connect(self) -> QdrantVectorStore:
        """Connects to embedded Qdrant or in-memory instance and initializes collection."""
        if self.vector_store is not None:
            return self.vector_store

        if self.force_memory:
            self.client = QdrantClient(location=":memory:")
            logger.info("Terhubung ke Qdrant In-Memory mode.")
        else:
            try:
                os.makedirs(self.qdrant_path, exist_ok=True)
                self.client = QdrantClient(path=self.qdrant_path)
                logger.info(f"Terhubung ke Qdrant embedded di {self.qdrant_path}")
            except Exception as e:
                logger.warning(f"Tidak dapat mengunci folder Qdrant ({e}). Beralih ke Qdrant In-Memory mode.")
                self.client = QdrantClient(location=":memory:")

        # Pastikan collection ada dengan konfigurasi Cosine distance
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )
            logger.info(f"Collection '{self.collection_name}' berhasil dibuat.")

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        return self.vector_store

    def ingest_document(
        self,
        text_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> int:
        """
        Splits text content into semantic chunks and ingests into Qdrant.
        Preserves metadata on all chunks.
        """
        if self.vector_store is None:
            self.connect()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(text_content)
        if not chunks:
            return 0

        base_meta = metadata.copy() if metadata else {"source": "Pedoman Medis BPJS"}
        chunk_metadatas = []
        for i in range(len(chunks)):
            m = base_meta.copy()
            m["chunk_index"] = i
            m["total_chunks"] = len(chunks)
            chunk_metadatas.append(m)

        self.vector_store.add_texts(chunks, metadatas=chunk_metadatas)
        logger.info(f"Berhasil mengindeks {len(chunks)} chunk ke koleksi '{self.collection_name}'.")
        return len(chunks)

    def ingest_documents(self, documents: List[Document]) -> int:
        """Ingests pre-constructed Document objects."""
        if self.vector_store is None:
            self.connect()
        if not documents:
            return 0
        self.vector_store.add_documents(documents)
        return len(documents)

    def search_rules(
        self,
        query: str,
        top_k: int = 3,
        as_text: bool = False,
        score_threshold: Optional[float] = None,
    ) -> Union[SearchResultList, str]:
        """
        Performs semantic similarity search against indexed clinical guidelines.
        Returns SearchResultList (behaving as List[Dict[str, Any]] and printable as text).
        """
        if self.vector_store is None:
            self.connect()

        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
            results = SearchResultList()
            for doc, score in docs_with_scores:
                sc = float(score)
                if score_threshold is not None and sc < score_threshold:
                    continue
                results.append({
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "Pedoman Medis BPJS"),
                    "score": sc,
                    "metadata": doc.metadata,
                })

            if as_text:
                return str(results)
            return results
        except Exception as e:
            logger.error(f"Error pencarian Vector DB: {e}")
            err_res = SearchResultList()
            if as_text:
                return f"Error pencarian Vector DB: {str(e)}"
            return err_res

    def format_rules_text(self, results: List[Dict[str, Any]]) -> str:
        """Helper to format search result dictionaries into string."""
        if not results:
            return "Tidak ada referensi PNPK yang ditemukan untuk kasus ini."
        if isinstance(results, SearchResultList):
            return str(results)
        temp_list = SearchResultList(results)
        return str(temp_list)

    def get_collection_info(self) -> Dict[str, Any]:
        """Returns collection metadata and point count."""
        if self.client is None:
            self.connect()
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": getattr(info, "points_count", 0),
                "status": getattr(info, "status", "unknown"),
                "vectors_count": getattr(info, "vectors_count", 0),
            }
        except Exception as e:
            return {"error": str(e)}


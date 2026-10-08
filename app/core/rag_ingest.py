"""Local, provenance-aware RAG document ingestion.

Uploaded documents stay under the local project data directory. The manifest is
content-addressed so re-uploading the same document does not index it twice.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pypdf import PdfReader

from app.core.vector_db import MedicalKnowledgeBase


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "Data RAG" / "uploads"
MANIFEST_PATH = PROJECT_ROOT / "knowledge_base" / "rag_manifest.json"
ALLOWED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt", ".json"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "document"


def _load_manifest() -> List[Dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_manifest(entries: List[Dict[str, Any]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = MANIFEST_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(MANIFEST_PATH)


def _extract_text(content: bytes, suffix: str) -> tuple[str, int | None]:
    if suffix == ".pdf":
        temp_path = UPLOAD_DIR / ".extracting.pdf"
        temp_path.write_bytes(content)
        try:
            reader = PdfReader(str(temp_path))
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                text = " ".join((page.extract_text() or "").split())
                if text:
                    pages.append(f"[Page {index}] {text}")
            return "\n\n".join(pages), len(reader.pages)
        finally:
            temp_path.unlink(missing_ok=True)

    text = content.decode("utf-8")
    if suffix == ".json":
        parsed = json.loads(text)
        text = json.dumps(parsed, ensure_ascii=False, indent=2)
    return text, None


def ingest_uploaded_document(
    content: bytes,
    filename: str,
    *,
    authority: str,
    effective_date: str,
    disease: str = "",
    icd10: str = "",
    rule_type: str = "",
) -> Dict[str, Any]:
    """Persist and index one local document, returning a safe manifest record."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Ukuran dokumen melebihi batas {MAX_UPLOAD_BYTES // 1024 // 1024} MB.")

    safe_name = _safe_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Format dokumen harus PDF, Markdown, TXT, atau JSON.")
    if not authority.strip() or not effective_date.strip():
        raise ValueError("Authority dan tanggal berlaku wajib diisi.")

    digest = hashlib.sha256(content).hexdigest()
    manifest = _load_manifest()
    duplicate = next((item for item in manifest if item.get("sha256") == digest), None)
    if duplicate:
        return {**duplicate, "duplicate": True}

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{digest[:16]}_{safe_name}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)
    text, page_count = _extract_text(content, suffix)
    if not text.strip():
        stored_path.unlink(missing_ok=True)
        raise ValueError("Dokumen tidak menghasilkan teks yang dapat diindeks.")

    document_id = f"doc_{digest[:16]}"
    metadata = {
        "document_id": document_id,
        "source": safe_name,
        "authority": authority.strip(),
        "effective_date": effective_date.strip(),
        "disease": disease.strip(),
        "icd10": icd10.strip(),
        "rule_type": rule_type.strip(),
        "sha256": digest,
    }
    kb = MedicalKnowledgeBase()
    chunk_count = kb.ingest_document(text, metadata=metadata)
    record = {
        **metadata,
        "stored_file": str(stored_path.relative_to(PROJECT_ROOT)),
        "file_type": suffix.lstrip("."),
        "page_count": page_count,
        "chunk_count": chunk_count,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "duplicate": False,
    }
    manifest.append(record)
    _save_manifest(manifest)
    return record


def list_ingested_documents() -> List[Dict[str, Any]]:
    """Return manifest metadata without document contents."""
    return _load_manifest()

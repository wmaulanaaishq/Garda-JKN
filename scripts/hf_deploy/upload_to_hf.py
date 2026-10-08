from huggingface_hub import HfApi
import os
api = HfApi(token=os.environ.get("HF_TOKEN"))
repo_id = "wmaulanaaishq/Garda-JKN-BPJS"
repo_type = "space"

# We must use proper fnmatch patterns for ignores
ignore_patterns = [
    ".git/*",
    ".git",
    "venv/*",
    "venv",
    "__pycache__/*",
    "*.pyc",
    ".agents/*",
    ".gemini/*",
    ".deepeval/*",
    ".env",
    "knowledge_base/qdrant_db/collection/pnpk_medical_rules/storage.sqlite-wal",
    "knowledge_base/qdrant_db/collection/pnpk_medical_rules/storage.sqlite-shm",
]

try:
    print("Uploading folder...")
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type=repo_type,
        ignore_patterns=ignore_patterns
    )
    print("Upload Success!")
except Exception as e:
    print(f"Error: {e}")

import os
from huggingface_hub import HfApi
from dotenv import load_dotenv

load_dotenv()
api = HfApi(token=os.environ.get("HF_TOKEN"))
repo_id = "wmaulanaaishq/Garda-JKN-BPJS"

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
    "frontend/*"
]

try:
    print(f"Uploading to {repo_id} (CPU Basic Space)...")
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=ignore_patterns
    )
    print("Upload Success!")
except Exception as e:
    print(f"Error: {e}")

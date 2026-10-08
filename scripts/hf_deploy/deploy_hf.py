import os
from huggingface_hub import HfApi
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("HF_TOKEN")
if not token:
    print("No HF_TOKEN found")
    exit(1)

api = HfApi(token=token)
repo_id = "wmaulanaaishq/Garda-JKN"
repo_type = "space"

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
    "frontend/node_modules/*"
]

try:
    print(f"Uploading folder to {repo_id}...")
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type=repo_type,
        ignore_patterns=ignore_patterns
    )
    print("Upload Success!")
except Exception as e:
    print(f"Error: {e}")

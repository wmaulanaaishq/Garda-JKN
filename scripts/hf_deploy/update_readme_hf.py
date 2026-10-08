import os
from huggingface_hub import HfApi
from dotenv import load_dotenv

load_dotenv()
api = HfApi(token=os.environ.get("HF_TOKEN"))
repo_id = "wmaulanaaishq/Garda-JKN"

try:
    print("Uploading fixed README...")
    api.upload_file(
        path_or_fileobj="README.md",
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="space"
    )
    print("Upload Success!")
except Exception as e:
    print(f"Error: {e}")

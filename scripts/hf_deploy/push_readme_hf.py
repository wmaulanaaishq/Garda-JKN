from huggingface_hub import HfApi
import os
api = HfApi(token=os.environ.get("HF_TOKEN"))
try:
    api.upload_file(
        path_or_fileobj="README.md",
        path_in_repo="README.md",
        repo_id="wmaulanaaishq/Garda-JKN-BPJS",
        repo_type="space"
    )
    print("README uploaded to Hugging Face!")
except Exception as e:
    print(f"Error: {e}")

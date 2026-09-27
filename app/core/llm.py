import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm():
    """
    Menginisialisasi LLM menggunakan AIML API dengan model DeepSeek R1.
    Sangat cocok untuk tugas penalaran medis dan deteksi upcoding kompleks.
    """
    api_key = os.getenv("AIML_API_KEY")
    if not api_key:
        raise ValueError("AIML_API_KEY tidak ditemukan di .env!")

    # AIML API menggunakan protokol yang kompatibel dengan OpenAI
    llm = ChatOpenAI(
        api_key=api_key,
        base_url="https://api.aimlapi.com/v1",
        model="deepseek/deepseek-r1",
        temperature=0.0, # Temperature 0 untuk penalaran klinis yang deterministik dan konsisten
        max_tokens=2048
    )
    
    return llm

"""GARDA-JKN LLM Configuration Module (AIML API / DeepSeek)."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm() -> ChatOpenAI:
    """Initializes ChatOpenAI client pointing to AIML API.

    Defaults to deepseek/deepseek-chat for ultra-fast, robust JSON adjudication.
    Can be configured to deepseek/deepseek-r1 via DEEPSEEK_MODEL in .env.
    """
    api_key = os.getenv("AIML_API_KEY")
    if not api_key:
        raise ValueError("AIML_API_KEY tidak ditemukan di .env!")

    model_name = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")
    max_tokens = 4096 if "r1" in model_name else 2048

    return ChatOpenAI(
        api_key=api_key,
        base_url="https://api.aimlapi.com/v1",
        model=model_name,
        temperature=0.0,
        max_tokens=max_tokens,
        timeout=60,
    )

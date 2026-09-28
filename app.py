import os
import gradio as gr
from fastapi import FastAPI
from api import app as fastapi_app

# Dummy function to trick ZeroGPU into not crashing if the user selected ZeroGPU hardware
try:
    import spaces
    @spaces.GPU
    def dummy_gpu():
        pass
except ImportError:
    pass

app = gr.mount_gradio_app(fastapi_app, gr.Interface(lambda x: f"GARDA-JKN FastAPI is running on HF Spaces! Status: OK.", "text", "text", title="GARDA-JKN Backend", description="This space serves the FastAPI backend for GARDA-JKN."), path="/")

# Do NOT call uvicorn.run() here, Hugging Face Gradio SDK does it automatically!

"""FastAPI server for Whisper transcription"""

import os
import platform

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from faster_whisper import WhisperModel

app = FastAPI()

def _get_whisper_runtime():
    """Infer a sensible Whisper runtime based on the host OS and env overrides."""
    device = os.getenv("WHISPER_DEVICE")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE")

    if device and compute_type:
        return device, compute_type

    system = platform.system().lower()

    if system == "darwin":
        # Apple Silicon (MacBook Air/Pro) should use Metal Performance Shaders.
        return device or "mps", compute_type or "float16"

    return device or "cuda", compute_type or "float16"


WHISPER_DEVICE, WHISPER_COMPUTE_TYPE = _get_whisper_runtime()
model = WhisperModel("large", device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
# Example CPU fallback:
# model = WhisperModel("medium", device="cpu", compute_type="int8")

class TranscribeRequest(BaseModel):
    file_path: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/transcribe/")
async def transcribe(request: TranscribeRequest):
    segments, info = model.transcribe(request.file_path)
    text = " ".join([segment.text.strip() for segment in segments])
    return {"text": text}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=4242)

if __name__ == "__main__":
    run_server()

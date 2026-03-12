"""FastAPI server for Whisper transcription"""

import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from faster_whisper import WhisperModel

app = FastAPI()

# Model configuration from environment variables
model_name = os.getenv('WHISPER_MODEL', 'large')
device = os.getenv('WHISPER_DEVICE', 'cuda')
compute_type = os.getenv('WHISPER_COMPUTE_TYPE', 'float16')

print(f"Loading Whisper model '{model_name}' on '{device}' with '{compute_type}'...")
model = WhisperModel(model_name, device=device, compute_type=compute_type)

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

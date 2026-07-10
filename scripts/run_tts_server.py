"""Pocket TTS HTTP server — directly sets tts_model before uvicorn."""
import sys, os, logging, io, threading
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Load model FIRST
print("Loading Pocket TTS model...", flush=True)
from pocket_tts import TTSModel
model = TTSModel.load_model(language="english", quantize=False)
print(f"Model loaded: {model.sample_rate}Hz, voice_cloning={model.has_voice_cloning}", flush=True)

# NOW create the server using the model directly
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import StreamingResponse
from queue import Queue
from pocket_tts.utils.utils import _ORIGINS_OF_PREDEFINED_VOICES
from pocket_tts.data.audio import stream_audio_chunks
import uvicorn

app = FastAPI(title="Pocket TTS")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/tts")
def tts(text: str = Form(...), voice: str = Form(None)):
    if not text.strip():
        raise HTTPException(400, "Text cannot be empty")
    voice = (voice or "alba").strip().lower()
    if voice in _ORIGINS_OF_PREDEFINED_VOICES:
        ms = model._cached_get_state_for_audio_prompt(voice)
    else:
        ms = model._cached_get_state_for_audio_prompt(voice)
    def gen():
        q = Queue()
        def fill():
            chunks = model.generate_audio_stream(model_state=ms, text_to_generate=text)
            class FL(io.IOBase):
                def __init__(s, q): s.q = q
                def write(s, d): s.q.put(d)
                def flush(s): pass
                def close(s): s.q.put(None)
            stream_audio_chunks(FL(q), chunks, model.sample_rate)
        t = threading.Thread(target=fill)
        t.start()
        while True:
            d = q.get()
            if d is None: break
            yield d
        t.join()
    return StreamingResponse(gen(), media_type="audio/wav")

print("Starting uvicorn...", flush=True)
tts_port = int(os.environ.get("TTS_PORT", "8000"))
uvicorn.run(app, host="localhost", port=tts_port, log_level="info")

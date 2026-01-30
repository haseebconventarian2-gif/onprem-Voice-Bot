# api/onprem.py
import os
import mimetypes
import tempfile
import subprocess
from typing import Optional

import httpx
from fastapi import HTTPException
import uuid


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return v


# -----------------------------
# LLM (Ollama)
# -----------------------------
def ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.1:8b")


async def generate_text(
    user_prompt: str,
    system_prompt: str | None = None,
    use_tools: bool = False,   # ignored on-prem (kept for compatibility)
    tool_results: dict | None = None,  # ignored (kept for compatibility)
) -> str:
    """
    Drop-in replacement for api.azure.generate_text()

    Uses Ollama chat API locally.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": str(system_prompt)})
    messages.append({"role": "user", "content": str(user_prompt or "")})

    payload = {
        "model": ollama_model(),
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        },
    }

    url = f"{ollama_base_url()}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            content = (data.get("message") or {}).get("content", "")
            return (content or "").strip() or "Sorry, I could not generate a response."
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}") from e


# -----------------------------
# STT (Whisper - faster-whisper)
# -----------------------------
def _whisper_model_name() -> str:
    # good defaults: "small", "medium", "large-v3"
    return os.getenv("WHISPER_MODEL", "small")


def _whisper_device() -> str:
    # "cpu" or "cuda"
    return os.getenv("WHISPER_DEVICE", "cpu")


def _whisper_compute_type() -> str:
    # cpu: "int8" or "float32", cuda: "float16"
    return os.getenv("WHISPER_COMPUTE_TYPE", "int8")


_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel  # lazy import
        _whisper_model = WhisperModel(
            _whisper_model_name(),
            device=_whisper_device(),
            compute_type=_whisper_compute_type(),
        )
    return _whisper_model


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    content_type: str | None,
    language: str | None = None,
) -> str:
    """
    Drop-in replacement for api.azure.transcribe_audio()

    Saves bytes to a temp file and runs faster-whisper locally.
    """
    if not audio_bytes:
        return ""

    inferred = content_type
    if not inferred:
        inferred, _ = mimetypes.guess_type(filename or "")
    suffix = ""
    if inferred:
        # best-effort suffix guessing
        if "mpeg" in inferred or "mp3" in inferred:
            suffix = ".mp3"
        elif "wav" in inferred:
            suffix = ".wav"
        elif "ogg" in inferred:
            suffix = ".ogg"
        elif "mp4" in inferred:
            suffix = ".mp4"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".audio") as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        model = _get_whisper_model()

        # If you want auto language detection, keep language=None
        # If you pass "en"/"ur" etc, it will bias.
        segments, info = model.transcribe(
            tmp_path,
            language=None if (language in (None, "", "auto")) else language,
            vad_filter=True,
        )
        text = "".join(seg.text for seg in segments).strip()
        return text
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Whisper STT error: {str(e)}") from e
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# -----------------------------
# TTS (Piper)
# -----------------------------
def audio_content_type() -> str:
    return "audio/wav"


def _piper_bin() -> str:
    # e.g. /usr/local/bin/piper  (Linux)
    # or C:\\piper\\piper.exe     (Windows)
    return _env("PIPER_BIN")


def _piper_model() -> str:
    # e.g. /models/en_US-lessac-medium.onnx
    return _env("PIPER_MODEL")


def _ffmpeg_bin() -> str:
    return os.getenv("FFMPEG_BIN", "ffmpeg")


def _has_ffmpeg() -> bool:
    try:
        subprocess.run([_ffmpeg_bin(), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False


PROJECT_ROOT = os.path.abspath(os.getcwd())
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def synthesize_speech(text: str, save_audio: bool = False) -> bytes:
    piper_bin = _piper_bin()
    piper_model = _piper_model()

    # Piper always writes WAV
    wav_path = os.path.join(
        OUTPUT_DIR if save_audio else tempfile.gettempdir(),
        f"tts_{uuid.uuid4().hex}.wav",
    )

    cmd = [
        piper_bin,
        "--model", piper_model,
        "--output_file", wav_path,
        "--debug",
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate((text or "").encode("utf-8"))

    if proc.returncode != 0:
        err_msg = (stderr or b"").decode("utf-8", errors="ignore").strip()
        raise RuntimeError(
            f"Piper TTS failed (code={proc.returncode}). "
            f"stderr='{err_msg}' out_path='{wav_path}' model='{piper_model}'"
        )

    if not os.path.exists(wav_path):
        raise RuntimeError(f"Piper did not produce output file: {wav_path}")

    with open(wav_path, "rb") as f:
        audio_bytes = f.read()

    if not save_audio:
        try:
            os.remove(wav_path)
        except OSError:
            pass

    return audio_bytes

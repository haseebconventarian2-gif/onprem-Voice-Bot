from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import Response, JSONResponse, HTMLResponse, FileResponse
from pathlib import Path
from datetime import datetime

from .onprem import (
    generate_text,
    transcribe_audio,
    synthesize_speech,
    audio_content_type,
)
from .onprem_search import build_rag_context

router = APIRouter(tags=["Chat"])

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)


@router.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@router.get(
    "/message_text",
    tags=["Chat"],
    summary="Text-only chat (RAG + LLM)",
    description="Returns JSON (no audio). Use this to test RAG + LLM quickly."
)
async def message_text(
    text: str = Query(..., description="User question/message")
):
    context = await build_rag_context(text)

    system_prompt = (
        "You are a helpful assistant. "
        "Answer using ONLY the provided context. "
        "If context is empty, say you do not know."
    )

    prompt = f"Context:\n{context}\n\nUser question:\n{text}\n"

    answer = await generate_text(
        user_prompt=prompt,
        system_prompt=system_prompt,
    )

    return JSONResponse(
        {
            "question": text,
            "answer": answer,
            "rag_context": context,
        }
    )


@router.post(
    "/message_audio",
    tags=["Chat"],
    summary="Audio input → STT → RAG → LLM → (optional) TTS",
    description=(
        "Upload an audio file. Server transcribes it with Whisper, retrieves context with RAG, "
        "generates an answer with Ollama, and returns audio bytes (wav/mp3 depending on config)."
    )
)
async def message_audio(
    file: UploadFile = File(...),
    save_audio: bool = Query(True, description="Save output audio to /outputs")
):
    audio_bytes = await file.read()
    user_text = await transcribe_audio(
        audio_bytes=audio_bytes,
        filename=file.filename,
        content_type=file.content_type,
    )

    if not user_text.strip():
        return JSONResponse({"error": "Could not transcribe audio"}, status_code=400)

    context = await build_rag_context(user_text)

    system_prompt = (
        "You are a helpful assistant. "
        "Answer using ONLY the provided context. "
        "If context is empty, say you do not know."
    )

    prompt = f"Context:\n{context}\n\nUser question:\n{user_text}\n"

    answer = await generate_text(
        user_prompt=prompt,
        system_prompt=system_prompt,
    )

    # Return speech audio
    audio_out = await synthesize_speech(answer, save_audio=save_audio)

    # Save a copy for UI retrieval
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext = "wav" if "wav" in audio_content_type() else "mp3"
    out_path = OUTPUTS_DIR / f"reply_{ts}.{ext}"
    out_path.write_bytes(audio_out)

    return Response(content=audio_out, media_type=audio_content_type())


@router.get(
    "/message_tts",
    tags=["Chat"],
    summary="Text → TTS only (Piper)",
    description="Useful to verify Piper works without involving RAG/LLM."
)
async def message_tts(
    text: str = Query(..., description="Text to convert to speech")
):
    audio_out = await synthesize_speech(text)
    return Response(content=audio_out, media_type=audio_content_type())


@router.get("/ui", response_class=HTMLResponse, tags=["UI"])
def ui_page():
    return HTMLResponse(
        """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>WhatsApp Web Style UI</title>
  <style>
    :root {
      --wa-green: #00a884;
      --wa-dark: #111b21;
      --wa-panel: #202c33;
      --wa-panel-2: #111b21;
      --wa-bg: #0b141a;
      --wa-chat-bg: #efeae2;
      --wa-chat-pattern: rgba(0,0,0,0.04);
      --wa-bubble-in: #d9fdd3;
      --wa-bubble-out: #ffffff;
      --wa-text: #111b21;
      --wa-muted: #667781;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
      background: var(--wa-bg);
      color: #e9edef;
      height: 100vh;
      display: flex;
      align-items: stretch;
    }
    .app {
      display: grid;
      grid-template-columns: 320px 1fr;
      width: 100%;
      height: 100vh;
    }
    .sidebar {
      background: var(--wa-panel-2);
      border-right: 1px solid #2a3942;
      display: flex;
      flex-direction: column;
    }
    .side-top {
      height: 60px;
      padding: 0 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--wa-panel);
    }
    .avatar {
      width: 36px; height: 36px; border-radius: 50%;
      background: #7a7a7a;
    }
    .side-search {
      padding: 10px;
      border-bottom: 1px solid #2a3942;
    }
    .search {
      background: #111b21;
      border: 1px solid #2a3942;
      border-radius: 8px;
      padding: 8px 10px;
      color: #e9edef;
      width: 100%;
    }
    .chat-list {
      flex: 1;
      overflow: auto;
    }
    .chat-item {
      display: flex;
      gap: 10px;
      padding: 12px 14px;
      border-bottom: 1px solid #2a3942;
      cursor: pointer;
    }
    .chat-item:hover { background: #1f2c33; }
    .chat-item .name { font-weight: 600; color: #e9edef; }
    .chat-item .last { color: var(--wa-muted); font-size: 12px; }
    .main {
      display: grid;
      grid-template-rows: 60px 1fr 62px;
      background: var(--wa-chat-bg);
      position: relative;
      overflow: hidden;
    }
    .main::before {
      content: "";
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(90deg, var(--wa-chat-pattern) 1px, transparent 1px),
        linear-gradient(var(--wa-chat-pattern) 1px, transparent 1px);
      background-size: 36px 36px;
      opacity: 0.5;
      pointer-events: none;
    }
    .main-top {
      background: var(--wa-panel);
      color: #e9edef;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 1;
    }
    .main-title { display: flex; align-items: center; gap: 10px; }
    .chat-area {
      padding: 16px 24px;
      overflow-y: auto;
      z-index: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .bubble {
      max-width: 70%;
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 14px;
      color: var(--wa-text);
      background: var(--wa-bubble-out);
      box-shadow: 0 1px 0 rgba(0,0,0,0.05);
    }
    .bubble.in {
      align-self: flex-start;
      background: var(--wa-bubble-out);
      border-top-left-radius: 2px;
    }
    .bubble.out {
      align-self: flex-end;
      background: var(--wa-bubble-in);
      border-top-right-radius: 2px;
    }
    .input-bar {
      background: var(--wa-panel);
      padding: 10px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      z-index: 1;
    }
    .btn {
      border: none;
      background: var(--wa-green);
      color: white;
      width: 42px;
      height: 42px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 18px;
    }
    .status {
      color: var(--wa-muted);
      font-size: 13px;
      flex: 1;
    }
    .voice-note {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 220px;
    }
    .voice-btn {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      border: none;
      background: #128c7e;
      color: white;
      font-size: 16px;
      cursor: pointer;
    }
    .voice-bar {
      flex: 1;
      height: 6px;
      background: #cfd6d4;
      border-radius: 999px;
      position: relative;
      overflow: hidden;
    }
    .voice-bar > span {
      display: block;
      height: 100%;
      width: 0%;
      background: #25d366;
    }
    .voice-time {
      font-size: 12px;
      color: #667781;
      min-width: 42px;
      text-align: right;
    }
    audio { display: none; }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="side-top">
        <div class="avatar"></div>
        <div>⋯</div>
      </div>
      <div class="side-search">
        <input class="search" placeholder="Search or start new chat" />
      </div>
      <div class="chat-list">
        <div class="chat-item">
          <div class="avatar"></div>
          <div>
            <div class="name">BankIslami Bot</div>
            <div class="last">Voice chat</div>
          </div>
        </div>
      </div>
    </aside>

    <main class="main">
      <div class="main-top">
        <div class="main-title">
          <div class="avatar"></div>
          BankIslami Bot
        </div>
        <div>⋮</div>
      </div>

      <div class="chat-area" id="chat">
        <div class="bubble in">Assalam‑o‑Alaikum! How can I help you?</div>
      </div>

      <div class="input-bar">
        <button class="btn" id="record">🎙</button>
        <button class="btn" id="stop" disabled>⏹</button>
        <button class="btn" id="send" disabled>➤</button>
        <div class="status" id="status">Idle</div>
      </div>
    </main>
  </div>

<script>
let mediaRecorder;
let chunks = [];
let recordedBlob;

const recordBtn = document.getElementById('record');
const stopBtn = document.getElementById('stop');
const sendBtn = document.getElementById('send');
const statusEl = document.getElementById('status');
const chat = document.getElementById('chat');

function addAudioBubble(blob, who) {
  const div = document.createElement('div');
  div.className = `bubble ${who}`;

  const wrap = document.createElement('div');
  wrap.className = 'voice-note';

  const btn = document.createElement('button');
  btn.className = 'voice-btn';
  btn.textContent = '▶';

  const bar = document.createElement('div');
  bar.className = 'voice-bar';
  const barFill = document.createElement('span');
  bar.appendChild(barFill);

  const time = document.createElement('div');
  time.className = 'voice-time';
  time.textContent = '0:00';

  const audio = document.createElement('audio');
  audio.src = URL.createObjectURL(blob);

  btn.onclick = () => {
    if (audio.paused) {
      audio.play();
      btn.textContent = '⏸';
    } else {
      audio.pause();
      btn.textContent = '▶';
    }
  };

  audio.onloadedmetadata = () => {
    const mins = Math.floor(audio.duration / 60);
    const secs = Math.floor(audio.duration % 60);
    time.textContent = `${mins}:${String(secs).padStart(2, '0')}`;
  };

  audio.ontimeupdate = () => {
    const pct = (audio.currentTime / audio.duration) * 100;
    barFill.style.width = `${pct}%`;
  };

  audio.onended = () => {
    btn.textContent = '▶';
    barFill.style.width = '0%';
  };

  wrap.appendChild(btn);
  wrap.appendChild(bar);
  wrap.appendChild(time);
  wrap.appendChild(audio);
  div.appendChild(wrap);

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

recordBtn.onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
  mediaRecorder.onstop = () => {
    recordedBlob = new Blob(chunks, { type: 'audio/webm' });
    addAudioBubble(recordedBlob, "out");
    sendBtn.disabled = false;
    statusEl.textContent = "Ready to send";
  };
  mediaRecorder.start();
  statusEl.textContent = "Recording...";
  recordBtn.disabled = true;
  stopBtn.disabled = false;
  sendBtn.disabled = true;
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
  recordBtn.disabled = false;
  stopBtn.disabled = true;
};

sendBtn.onclick = async () => {
  if (!recordedBlob) return;

  statusEl.textContent = "Sending...";
  sendBtn.disabled = true;

  const form = new FormData();
  form.append('file', recordedBlob, 'recording.webm');

  const waitDiv = document.createElement('div');
  waitDiv.className = "bubble in";
  waitDiv.textContent = "Please wait…";
  chat.appendChild(waitDiv);
  chat.scrollTop = chat.scrollHeight;

  const res = await fetch('/message_audio', { method: 'POST', body: form });
  if (!res.ok) {
    waitDiv.textContent = "Error sending audio";
    statusEl.textContent = "Error";
    return;
  }

  const audioBlob = await res.blob();
  const replyBubble = addAudioBubble(audioBlob, "in");
  waitDiv.replaceWith(replyBubble);

  statusEl.textContent = "Idle";
  recordedBlob = null;
};
</script>
</body>
</html>
        """
    )


@router.get("/ui/latest_audio", tags=["UI"])
def latest_audio():
    files = sorted(OUTPUTS_DIR.glob("reply_*.*"))
    if not files:
        return JSONResponse({"error": "No audio available"}, status_code=404)
    return FileResponse(path=files[-1], media_type=audio_content_type())

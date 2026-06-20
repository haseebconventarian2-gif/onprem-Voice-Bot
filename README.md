<div align="center">

# On-Premises Voice Bot

On-premises banking voice bot with local FAISS retrieval, document-based responses, and WhatsApp integration.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Reference%20Implementation-6366F1)

</div>

---

## Overview

On-premises banking voice bot with local FAISS retrieval, document-based responses, and WhatsApp integration.

## Highlights

- Local Ollama inference
- FAISS knowledge retrieval
- Offline speech recognition
- FastAPI and WhatsApp endpoints

## Tech Stack

Python Â· FastAPI Â· Ollama Â· FAISS Â· faster-whisper

## Getting Started

```bash
git clone https://github.com/haseebconventarian2-gif/onprem-Voice-Bot.git
cd onprem-Voice-Bot
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Configure Ollama, Whisper, optional Piper, and WhatsApp values in `.env`.

> Store credentials in `.env` and never commit secrets.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Status

This is a learning and reference implementation. Review security, validation, monitoring, and deployment settings before production use.

## Detailed Code Reference

**Runtime flow:** `Text/audio -> local STT -> context -> Ollama -> local TTS/text`

### Repository map

- `bank.json` - project file
- `build_faiss_index.py` - project file
- `chunks.json` - project file
- `faiss.index` - project file
- `main.py` - project file
- `onprem.py` - project file
- `onprem_search.py` - project file
- `README.md` - project file
- `requirements.txt` - project file
- `routes.py` - project file
- `whatsapp.py` - project file

### Validation checklist

1. Install dependencies in a clean virtual environment.
2. Configure only the environment variables needed by enabled integrations.
3. Start the documented entry point and test its health or root route.
4. Exercise successful and invalid requests.
5. Confirm secrets, private datasets, indexes, and model artifacts are ignored.

### Production checklist

- Use managed secret storage.
- Add authentication, authorization, rate limiting, and request-size limits.
- Add automated tests, structured logs, monitoring, and health checks.
- Pin and audit dependencies.
- Define retention and privacy controls for audio and customer data.

> This README reflects the current codebase. External AI, telephony, and messaging features require their respective accounts, assets, and approvals.


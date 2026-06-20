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

Python · FastAPI · Ollama · FAISS · faster-whisper

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

<!-- code-audit-details -->

## 🔄 Runtime Flow

`Text/audio → local STT → context retrieval → Ollama → local TTS/text`

This flow is derived from the current entry points and service calls.

## 🗂 Code Map

| Path | Responsibility |
| --- | --- |
| `bank.json` | Supporting resource |
| `build_faiss_index.py` | Supporting resource |
| `chunks.json` | Supporting resource |
| `main.py` | Application entry point |
| `onprem.py` | Supporting resource |
| `onprem_search.py` | Supporting resource |
| `requirements.txt` | Python dependencies |
| `routes.py` | HTTP routes and orchestration |
| `whatsapp.py` | WhatsApp integration |

## 🔐 Environment Variables

No environment-variable reads were detected.

## 🌐 Detected API Routes

| Method | Endpoint |
| --- | --- |
| `GET` | `/` |
| `GET` | `/health` |
| `GET` | `/ui` |
| `GET` | `/ui/latest_audio` |
| `GET` | `/webhook` |
| `POST` | `/webhook` |

## 🧪 Validation Guide

1. Install dependencies in a clean virtual environment.
2. Start the documented entry point and test the root or health route.
3. Exercise one valid and one invalid request.
4. Verify external-service errors are handled clearly.
5. Confirm secrets, private data, indexes, and model artifacts are ignored.

## 🔒 Production Checklist

- Use managed secret storage and rotate exposed credentials.
- Add authentication, authorization, rate limiting, and request-size limits.
- Add automated tests, structured logging, monitoring, and health checks.
- Pin and audit dependencies.
- Define retention and privacy controls for audio and customer data.

## ⚠️ Code-Audit Notes

- Documentation reflects the current repository code and may expose integrations that need separate cloud accounts, model assets, or channel approval.
- Treat the project as a reference implementation until its security and deployment configuration are hardened.

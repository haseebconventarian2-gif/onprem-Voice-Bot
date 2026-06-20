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

<div align="center">

# On-Premises Voice Bot

On-premises banking voice bot with local FAISS retrieval, document-based responses, and WhatsApp integration.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white&style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Reference%20Implementation-6366F1?style=for-the-badge)

[Story](#-the-story) · [Features](#-features) · [Setup](#-getting-started) · [Configuration](#-configuration)

</div>

---

## 🎯 Overview

On-premises banking voice bot with local FAISS retrieval, document-based responses, and WhatsApp integration.

## 📖 The Story

Cloud voice assistants are convenient, but some organizations need customer audio and documents to remain inside their own infrastructure. This project asks whether a complete conversational path—retrieval, language generation, transcription, and speech—can run locally.

The answer is assembled from focused components: FAISS and Sentence Transformers retrieve banking knowledge, Ollama runs the language model, faster-whisper handles speech recognition, and Piper can synthesize the reply. FastAPI and WhatsApp modules expose the local intelligence to applications and messaging workflows.

The repository demonstrates a privacy-oriented alternative to cloud-first voice bots. Its next chapter is packaging the model assets, benchmarking latency on target hardware, encrypting stored audio, and adding a clear offline deployment guide.

## ✨ Features

- Local Ollama inference
- FAISS knowledge retrieval
- Offline speech recognition
- FastAPI and WhatsApp endpoints

## 🧰 Tech Stack

| Technology | Purpose |
| --- | --- |
| **Python** | Primary programming language |
| **FastAPI** | API and web server |
| **Ollama** | Local language-model runtime |
| **FAISS** | Vector similarity search |
| **faster-whisper** | Local speech recognition |

## 🚀 Getting Started

```bash
git clone https://github.com/haseebconventarian2-gif/onprem-Voice-Bot.git
cd onprem-Voice-Bot
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ Configuration

Configure Ollama, Whisper, optional Piper, and WhatsApp values in `.env`.

> Store credentials in `.env` and never commit secrets.

## ▶️ Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📌 Project Status

This is a learning and reference implementation. Review security, validation, monitoring, and deployment settings before production use.

## 🧩 Detailed Code Reference

**Runtime flow:** `Text/audio -> local STT -> context -> Ollama -> local TTS/text`

### 📁 Repository Map

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

## 🧪 Validation Checklist

1. Install dependencies in a clean virtual environment.
2. Configure only the environment variables needed by enabled integrations.
3. Start the documented entry point and test its health or root route.
4. Exercise successful and invalid requests.
5. Confirm secrets, private datasets, indexes, and model artifacts are ignored.

## 🔒 Production Checklist

- Use managed secret storage.
- Add authentication, authorization, rate limiting, and request-size limits.
- Add automated tests, structured logs, monitoring, and health checks.
- Pin and audit dependencies.
- Define retention and privacy controls for audio and customer data.

> This README reflects the current codebase. External AI, telephony, and messaging features require their respective accounts, assets, and approvals.




## 🛠 Troubleshooting

<details>
<summary><strong>The application does not start</strong></summary>

Confirm the virtual environment is active, install `requirements.txt`, and check that every required environment variable is defined.
</details>

<details>
<summary><strong>An AI or messaging service cannot be reached</strong></summary>

Verify the endpoint, credentials, deployment names, network access, and external service status. Restart the application after changing `.env`.
</details>

<details>
<summary><strong>A model, index, or artifact is missing</strong></summary>

Run the repository's documented build or training step and confirm that generated files are stored at the paths expected by the code.
</details>

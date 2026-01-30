from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
print("PIPER_BIN=", os.getenv("PIPER_BIN"))
print("PIPER_MODEL=", os.getenv("PIPER_MODEL"))



from fastapi import FastAPI
from api.routes import router as api_router
from api.whatsapp import router as whatsapp_router

app = FastAPI(title="On-Prem WhatsApp RAG Bot")

app.include_router(api_router)
app.include_router(whatsapp_router)

@app.get("/")
def health():
    return {"status": "ok"}

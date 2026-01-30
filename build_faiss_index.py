# scripts/build_faiss_index.py
import os
import json
import glob
from typing import List, Dict, Tuple, Any

import numpy as np
import faiss

from dotenv import load_dotenv
load_dotenv()


import logging
logging.getLogger("sentence_transformers").setLevel(logging.CRITICAL)
logging.getLogger("transformers").setLevel(logging.CRITICAL)



KB_PATH = os.getenv("KB_PATH", "./kb")
KB_INDEX_DIR = os.getenv("KB_INDEX_DIR", "./kb_index")
EMBEDDING_MODEL = os.getenv("LOCAL_EMBED_MODEL_PATH", "models/all-MiniLM-L6-v2")


CHUNK_SIZE = int(os.getenv("KB_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("KB_CHUNK_OVERLAP", "150"))

# Which fields to use from JSON objects (in priority order)
JSON_TEXT_FIELDS = [s.strip() for s in os.getenv("JSON_TEXT_FIELDS", "text,content,body,answer").split(",")]
JSON_TITLE_FIELDS = [s.strip() for s in os.getenv("JSON_TITLE_FIELDS", "title,question,name").split(",")]
JSON_ID_FIELDS = [s.strip() for s in os.getenv("JSON_ID_FIELDS", "id,doc_id,_id").split(",")]


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf_file(path: str) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        raise RuntimeError("PDF support requires 'pypdf'. Install it or remove PDFs from kb/.")

    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _first_present(obj: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in obj and obj[k] is not None:
            v = obj[k]
            if isinstance(v, (dict, list)):
                continue
            s = str(v).strip()
            if s:
                return s
    return ""


def _read_json_file(path: str) -> List[Tuple[str, str]]:
    """
    Supports your format:
    [
      {
        "id": "...",
        "source": {...},
        "content": {"title": "...", "text": "..."},
        "metadata": {...}
      }
    ]
    Returns list of (source_label, full_text).
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise RuntimeError(
            f"Unsupported JSON structure in {path}. Expected a top-level list."
        )

    outputs: List[Tuple[str, str]] = []
    rel = os.path.relpath(path, KB_PATH)

    for i, rec in enumerate(data):
        if not isinstance(rec, dict):
            continue

        rid = str(rec.get("id") or i)

        content = rec.get("content") or {}
        if not isinstance(content, dict):
            content = {}

        title = str(content.get("title") or "").strip()
        text = str(content.get("text") or "").strip()

        if not text:
            continue

        # Create a meaningful "source" label for citations in RAG output
        src = rec.get("source") or {}
        if isinstance(src, dict):
            page = str(src.get("page") or "").strip()
            section = str(src.get("section") or "").strip()
            url = str(src.get("url") or "").strip()
        else:
            page = section = url = ""

        source_label_parts = [f"{rel}#{rid}"]
        if page:
            source_label_parts.append(page)
        if section:
            source_label_parts.append(section)
        if url:
            source_label_parts.append(url)

        source_label = " | ".join(source_label_parts)

        full_text = f"{title}\n\n{text}" if title else text
        outputs.append((source_label, full_text))

    return outputs



def _load_docs() -> List[Tuple[str, str]]:
    """
    Returns list of (source_name, full_text)
    """
    paths = []
    paths += glob.glob(os.path.join(KB_PATH, "**/*.txt"), recursive=True)
    paths += glob.glob(os.path.join(KB_PATH, "**/*.md"), recursive=True)
    paths += glob.glob(os.path.join(KB_PATH, "**/*.pdf"), recursive=True)
    paths += glob.glob(os.path.join(KB_PATH, "**/*.json"), recursive=True)

    docs: List[Tuple[str, str]] = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()

        if ext in [".txt", ".md"]:
            txt = _read_text_file(p).strip()
            if txt:
                docs.append((os.path.relpath(p, KB_PATH), txt))

        elif ext == ".pdf":
            txt = _read_pdf_file(p).strip()
            if txt:
                docs.append((os.path.relpath(p, KB_PATH), txt))

        elif ext == ".json":
            for source_label, txt in _read_json_file(p):
                txt = (txt or "").strip()
                if txt:
                    docs.append((source_label, txt))

    return docs


def _chunk(text: str) -> List[str]:
    text = " ".join((text or "").split())
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        j = min(len(text), i + CHUNK_SIZE)
        chunks.append(text[i:j])
        if j == len(text):
            break
        i = max(0, j - CHUNK_OVERLAP)
    return chunks


def _embed(texts: List[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")


def main():
    os.makedirs(KB_INDEX_DIR, exist_ok=True)
    docs = _load_docs()
    if not docs:
        raise RuntimeError(f"No documents found in {KB_PATH}. Add docs under kb/ then re-run.")

    chunks_meta: List[Dict] = []
    chunks_text: List[str] = []

    for source, txt in docs:
        for ch in _chunk(txt):
            chunks_text.append(ch)
            chunks_meta.append({"source": source, "text": ch})

    vectors = _embed(chunks_text)
    d = vectors.shape[1]

    # cosine similarity via inner product (normalized embeddings)
    index = faiss.IndexFlatIP(d)
    index.add(vectors)

    faiss.write_index(index, os.path.join(KB_INDEX_DIR, "faiss.index"))
    with open(os.path.join(KB_INDEX_DIR, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks_meta, f, ensure_ascii=False, indent=2)

    print(f"✅ Built index with {len(chunks_text)} chunks")
    print(f"   Index: {os.path.join(KB_INDEX_DIR, 'faiss.index')}")
    print(f"   Meta : {os.path.join(KB_INDEX_DIR, 'chunks.json')}")


if __name__ == "__main__":
    main()
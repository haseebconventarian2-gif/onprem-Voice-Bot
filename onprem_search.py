# api/onprem_search.py
import os
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

import numpy as np
import faiss

from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(
    level=os.getenv("RAG_LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("rag")


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def kb_index_dir() -> str:
    return os.getenv("KB_INDEX_DIR", "./kb_index")


@dataclass
class KBStore:
    index: faiss.Index
    chunks: List[Dict]  # each chunk: {"text":..., "source":...}


_store: Optional[KBStore] = None


def _load_store() -> KBStore:
    global _store
    if _store is not None:
        log.debug("Using cached KB store")
        return _store

    idx_path = os.path.join(kb_index_dir(), "faiss.index")
    meta_path = os.path.join(kb_index_dir(), "chunks.json")

    log.info("Loading KB index")
    log.info("KB_INDEX_DIR=%s", kb_index_dir())
    log.info("faiss.index=%s", idx_path)
    log.info("chunks.json=%s", meta_path)

    if not os.path.exists(idx_path) or not os.path.exists(meta_path):
        raise RuntimeError(
            f"KB index not found. Build it first. Missing: {idx_path} or {meta_path}\n"
            "Run: python scripts/build_faiss_index.py"
        )

    index = faiss.read_index(idx_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    log.info("Loaded index with %d chunks", len(chunks))
    _store = KBStore(index=index, chunks=chunks)
    return _store


_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        model_path = os.getenv("LOCAL_EMBED_MODEL_PATH", "models/all-MiniLM-L6-v2")
        log.info("Loading embedder from %s", model_path)
        _embedder = SentenceTransformer(model_path)
        log.info("Embedder loaded")
    return _embedder


def _embed(texts: List[str]) -> np.ndarray:
    log.debug("Embedding %d texts", len(texts))
    model = _get_embedder()
    vecs = model.encode(texts, normalize_embeddings=True)
    log.debug("Embedding shape: %s", getattr(vecs, "shape", None))
    return np.asarray(vecs, dtype="float32")


async def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict]:
    """
    Local vector search against FAISS.
    Returns: [{"content":..., "score":..., "source":...}, ...]
    """
    if not query or not query.strip():
        log.warning("Empty query")
        return []

    log.info("RAG search: top_k=%d, query='%s'", top_k, query[:200])
    store = _load_store()
    qv = _embed([query])  # (1, d)

    D, I = store.index.search(qv, top_k)

    docs: List[Dict] = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0 or idx >= len(store.chunks):
            continue
        ch = store.chunks[idx]
        docs.append(
            {
                "content": ch.get("text", ""),
                "score": float(score),
                "source": ch.get("source", "KB"),
            }
        )

    log.info("RAG results: %d docs", len(docs))
    log.info("RAG results full:\n%s", json.dumps(docs, ensure_ascii=False, indent=2))
    return docs


async def build_rag_context(query: str) -> str:
    """
    Formats retrieved chunks exactly like your Azure version.
    """
    docs = await search_knowledge_base(query, top_k=int(os.getenv("KB_TOP_K", "5")))
    if not docs:
        log.info("RAG context: empty")
        return ""

    parts = []
    for doc in docs:
        parts.append(
            f"Source: {doc['source']} (Relevance: {doc['score']:.2f})\n"
            f"Content: {doc['content']}"
        )
    context = "\n\n".join(parts)
    log.info("RAG context length: %d chars", len(context))
    log.info("RAG context full:\n%s", context)
    return context


async def search_tool(query: str) -> Dict:
    """
    Compatibility function (your old azure tool-calling path expects this signature).
    """
    docs = await search_knowledge_base(query, top_k=3)
    if not docs:
        return {"status": "no_results", "message": "No relevant information found in knowledge base"}

    return {
        "status": "success",
        "results": [
            {"source": d["source"], "content": d["content"], "confidence": d["score"]}
            for d in docs
        ],
    }




if __name__ == "__main__":
    import asyncio

    test_query = os.getenv("RAG_TEST_QUERY", "What is BankIslami?")
    print(f"Running RAG test with query: {test_query}")

    async def _run():
        ctx = await build_rag_context(test_query)
        print("\n--- RAG CONTEXT START ---\n")
        print(ctx)
        print("\n--- RAG CONTEXT END ---\n")

    asyncio.run(_run())

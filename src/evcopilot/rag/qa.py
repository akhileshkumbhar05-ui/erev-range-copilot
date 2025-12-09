# src/evcopilot/rag/qa.py

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import requests
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Paths and config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INDEX_DIR = PROJECT_ROOT / "data" / "knowledge_base"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
CHUNKS_META_PATH = INDEX_DIR / "chunks_meta.json"

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# Ollama config – defaults are for local development.
# You can still override these with environment variables if needed.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
# IMPORTANT: keep this in sync with the model you actually pulled via `ollama pull`
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class RAGIndexNotFoundError(RuntimeError):
    pass


# Cache the embedding model at module load
_embedding_model: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        print(f"[RAG] Loading embedding model: {EMBED_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedding_model


def load_index() -> Tuple[np.ndarray, List[dict]]:
    if not EMBEDDINGS_PATH.exists() or not CHUNKS_META_PATH.exists():
        raise RAGIndexNotFoundError(
            f"RAG index not found in {INDEX_DIR}. "
            "Run `python scripts/build_knowledge_base.py` first."
        )

    embeddings = np.load(EMBEDDINGS_PATH)
    with CHUNKS_META_PATH.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    chunks_meta = meta["chunks"]
    return embeddings, chunks_meta


def _embed_query(query: str) -> np.ndarray:
    model = _get_embedding_model()
    vec = model.encode([query], convert_to_numpy=True)[0]
    return vec.astype("float32")


def search_similar_chunks(
    query: str,
    embeddings: np.ndarray,
    chunks_meta: List[dict],
    top_k: int = 4,
) -> List[RetrievedChunk]:
    q_vec = _embed_query(query)

    # cosine similarity
    emb_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
    scores = emb_norm @ q_norm

    top_idx = np.argsort(scores)[::-1][:top_k]

    results: List[RetrievedChunk] = []
    for idx in top_idx:
        meta = chunks_meta[int(idx)]
        results.append(
            RetrievedChunk(
                text=meta["text"],
                source=meta["source"],
                score=float(scores[idx]),
            )
        )
    return results


def _build_system_prompt() -> str:
    return (
        "You are 'EREV Copilot', a technical assistant for an academic project on "
        "Extended-Range Electric Vehicles (EREVs), EV miles electrification, CO2 "
        "savings, and transportation costs.\n\n"
        "Use ONLY the provided context and basic arithmetic. If something is not in "
        "the context, say you don't know instead of guessing.\n\n"
        "Explain clearly and concisely, and whenever possible relate answers to:\n"
        "- share of EV miles vs total VMT,\n"
        "- range trade-offs (short-range BEV, EREV, long-range BEV),\n"
        "- emissions and cost per mile.\n"
    )


def _format_context(chunks: List[RetrievedChunk]) -> str:
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(
            f"[Chunk {i} | score={c.score:.3f} | source={c.source}]\n{c.text}\n"
        )
    return "\n\n".join(blocks)


def _call_ollama_chat(prompt: str) -> str:
    """
    Call the local Ollama HTTP API in non-streaming mode.
    """
    url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        resp = requests.post(url, json=payload, timeout=300)
    except requests.RequestException as e:
        # Network / connection-level problems
        raise RuntimeError(
            f"Error calling Ollama at {url}: {e}. "
            "Is Ollama installed and running locally?"
        ) from e

    if resp.status_code != 200:
        # Surface the Ollama error body to help debugging in Streamlit
        try:
            err_body = resp.text
        except Exception:
            err_body = "<unable to read response body>"
        raise RuntimeError(
            f"Ollama returned HTTP {resp.status_code} for {url}. "
            f"Response body: {err_body}"
        )

    data = resp.json()
    try:
        return data["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(
            f"Unexpected Ollama response format: {data}"
        ) from e


def answer_question(
    query: str,
    embeddings: np.ndarray,
    chunks_meta: List[dict],
    top_k: int = 4,
) -> Tuple[str, List[RetrievedChunk]]:
    """
    Run retrieval + local LLM via Ollama. Returns (answer, retrieved_chunks).
    """
    if not query.strip():
        raise ValueError("Query is empty.")

    retrieved = search_similar_chunks(query, embeddings, chunks_meta, top_k=top_k)
    context = _format_context(retrieved)

    prompt = (
        "Answer the question using ONLY the context below. "
        "If there is missing information, be explicit about what is unknown.\n\n"
        f"Question:\n{query}\n\n"
        f"Context:\n{context}"
    )

    answer = _call_ollama_chat(prompt)
    return answer, retrieved

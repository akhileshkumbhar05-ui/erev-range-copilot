# src/evcopilot/rag/indexer.py

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ---- Paths ----

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = PROJECT_ROOT / "docs" / "knowledge_base"
INDEX_DIR = PROJECT_ROOT / "data" / "knowledge_base"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
CHUNKS_META_PATH = INDEX_DIR / "chunks_meta.json"

# Small, fast, open-source embedding model
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass
class Chunk:
    doc_id: str
    chunk_id: int
    text: str
    source: str  # relative path


# ---- Utilities ----

def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages)


def _read_doc(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _read_txt(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    # ignore other types for now
    return ""


def _chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    text = " ".join(text.split())  # collapse whitespace
    chunks: List[str] = []
    start = 0
    n = len(text)
    if n == 0:
        return chunks

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chars - overlap
        if start >= n:
            break
    return chunks


def _iter_documents() -> Iterable[Path]:
    if not DOCS_DIR.exists():
        raise FileNotFoundError(
            f"docs/knowledge_base not found at {DOCS_DIR}. "
            "Create the folder and copy your EREV paper / docs into it."
        )
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix.lower() in {".pdf", ".txt", ".md"}:
            yield path


# ---- Embedding + index build ----

def build_knowledge_base(batch_size: int = 16) -> None:
    """
    Read all docs from docs/knowledge_base/*, chunk them, embed chunks
    using an open-source sentence-transformers model, and write a simple
    index under data/knowledge_base/.
    """
    print(f"[RAG] Loading embedding model: {EMBED_MODEL_NAME}")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    chunks: List[Chunk] = []
    all_texts: List[str] = []

    print(f"[RAG] Scanning documents in {DOCS_DIR}...")
    for doc_idx, path in enumerate(_iter_documents()):
        rel = str(path.relative_to(PROJECT_ROOT))
        print(f"[RAG] Reading #{doc_idx + 1}: {rel}")
        doc_text = _read_doc(path)
        doc_chunks = _chunk_text(doc_text)
        for i, ch in enumerate(doc_chunks):
            chunk = Chunk(
                doc_id=f"doc-{doc_idx}",
                chunk_id=i,
                text=ch,
                source=rel,
            )
            chunks.append(chunk)
            all_texts.append(ch)

    if not chunks:
        raise RuntimeError(
            "No usable text chunks were created. "
            "Check that docs/knowledge_base has .pdf/.txt/.md files with text."
        )

    print(f"[RAG] Total chunks to embed: {len(chunks)}")

    # sentence-transformers encodes everything locally
    embeddings = model.encode(
        all_texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    embeddings = embeddings.astype("float32")
    print(f"[RAG] Embeddings shape: {embeddings.shape}")

    # Save embeddings
    np.save(EMBEDDINGS_PATH, embeddings)

    # Save metadata
    meta_payload = {
        "model": EMBED_MODEL_NAME,
        "chunks": [
            {
                "doc_id": c.doc_id,
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source": c.source,
            }
            for c in chunks
        ],
    }
    with CHUNKS_META_PATH.open("w", encoding="utf-8") as f:
        json.dump(meta_payload, f, ensure_ascii=False, indent=2)

    print(f"[RAG] Saved embeddings to {EMBEDDINGS_PATH}")
    print(f"[RAG] Saved metadata to    {CHUNKS_META_PATH}")
    print("[RAG] Knowledge base build complete.")


def main() -> None:
    build_knowledge_base()


if __name__ == "__main__":
    main()

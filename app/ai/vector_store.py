"""
app/ai/vector_store.py

ChromaDB-backed knowledge store for NetMonitor.

Responsibilities:
  - Ingest all markdown files under knowledge/ into a persistent ChromaDB collection
  - Embed documents using sentence-transformers (all-MiniLM-L6-v2, fully local)
  - Expose semantic_retrieve() for LangGraph nodes to query at runtime

Collection is rebuilt only when knowledge files change (hash-based cache check).
No external API calls — everything runs locally.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.utils.logger import logger

# ── Constants ────────────────────────────────────────────────────────────────

COLLECTION_NAME = "netmonitor_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # 80 MB, CPU-friendly, fully local
CHROMA_PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / ".chroma_db"
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent.parent / "knowledge"
HASH_CACHE_FILE = CHROMA_PERSIST_DIR / "knowledge_hash.json"

# ── Module-level singletons (lazy-initialised) ───────────────────────────────

_embedder: Optional[SentenceTransformer] = None
_collection: Optional[chromadb.Collection] = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading sentence-transformer model: %s", EMBED_MODEL_NAME)
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _get_client() -> chromadb.PersistentClient:
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


# ── Knowledge file discovery and hashing ─────────────────────────────────────

def _discover_knowledge_files() -> list[Path]:
    """Return all .md files under knowledge/ sorted for deterministic ordering."""
    return sorted(KNOWLEDGE_ROOT.rglob("*.md"))


def _compute_knowledge_hash(files: list[Path]) -> str:
    """SHA-256 over all file paths + contents — detects any addition, edit, or deletion."""
    h = hashlib.sha256()
    for f in files:
        h.update(str(f).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def _load_hash_cache() -> dict:
    try:
        return json.loads(HASH_CACHE_FILE.read_text()) if HASH_CACHE_FILE.exists() else {}
    except Exception:
        return {}


def _save_hash_cache(data: dict) -> None:
    try:
        HASH_CACHE_FILE.write_text(json.dumps(data))
    except Exception as e:
        logger.warning("Could not save knowledge hash cache: %s", e)


# ── Document chunking ─────────────────────────────────────────────────────────

def _chunk_markdown(text: str, source: str, max_chars: int = 800) -> list[dict]:
    """
    Split a markdown file into chunks at heading boundaries first,
    then by character limit. Returns list of {text, source, chunk_id}.

    Heading-aware splitting keeps semantically coherent sections together
    (e.g. a full 'Diagnosis' subsection stays in one chunk).
    """
    import re
    # Split on any markdown heading (##, ###, etc.)
    sections = re.split(r"\n(?=#{1,4} )", text.strip())
    chunks = []
    chunk_idx = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue
        # If a section is within the character limit, keep it whole
        if len(section) <= max_chars:
            chunks.append({
                "text": section,
                "source": source,
                "chunk_id": f"{source}::{chunk_idx}",
            })
            chunk_idx += 1
        else:
            # Hard-split oversized sections by paragraph
            paragraphs = re.split(r"\n{2,}", section)
            buffer = ""
            for para in paragraphs:
                if len(buffer) + len(para) + 2 <= max_chars:
                    buffer = (buffer + "\n\n" + para).strip()
                else:
                    if buffer:
                        chunks.append({
                            "text": buffer,
                            "source": source,
                            "chunk_id": f"{source}::{chunk_idx}",
                        })
                        chunk_idx += 1
                    buffer = para.strip()
            if buffer:
                chunks.append({
                    "text": buffer,
                    "source": source,
                    "chunk_id": f"{source}::{chunk_idx}",
                })
                chunk_idx += 1

    return chunks


# ── Ingestion ─────────────────────────────────────────────────────────────────

def _ingest(collection: chromadb.Collection, files: list[Path]) -> None:
    """Embed and upsert all knowledge file chunks into the collection."""
    embedder = _get_embedder()
    all_chunks: list[dict] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Skipping unreadable knowledge file %s: %s", f, e)
            continue

        # Use relative path as source label (e.g. "runbooks/high_latency.md")
        source = str(f.relative_to(KNOWLEDGE_ROOT))
        chunks = _chunk_markdown(text, source)
        all_chunks.extend(chunks)
        logger.debug("Chunked %s → %d chunks", source, len(chunks))

    if not all_chunks:
        logger.warning("No knowledge chunks to ingest — knowledge/ folder may be empty.")
        return

    texts = [c["text"] for c in all_chunks]
    ids = [c["chunk_id"] for c in all_chunks]
    metadatas = [{"source": c["source"]} for c in all_chunks]

    logger.info("Embedding %d chunks with %s ...", len(texts), EMBED_MODEL_NAME)
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    # Upsert in batches of 100 to avoid memory spikes
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            documents=texts[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )

    logger.info("Ingested %d chunks into ChromaDB collection '%s'", len(texts), COLLECTION_NAME)


# ── Public API ────────────────────────────────────────────────────────────────

def get_collection() -> chromadb.Collection:
    """
    Return the ChromaDB collection, rebuilding it if knowledge files have changed.
    Safe to call multiple times — rebuilds only when necessary.
    """
    global _collection
    client = _get_client()

    files = _discover_knowledge_files()
    current_hash = _compute_knowledge_hash(files) if files else "empty"
    cache = _load_hash_cache()

    needs_rebuild = (
        _collection is None
        or cache.get("hash") != current_hash
    )

    if needs_rebuild:
        logger.info("Knowledge base changed or first run — rebuilding ChromaDB collection.")
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # Collection didn't exist yet
        _collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        _ingest(_collection, files)
        _save_hash_cache({"hash": current_hash, "chunks": _collection.count()})
    else:
        if _collection is None:
            _collection = client.get_collection(COLLECTION_NAME)
        logger.debug("ChromaDB collection up-to-date (%d chunks).", _collection.count())

    return _collection


def semantic_retrieve(query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieve the top-n most semantically relevant knowledge chunks for a query.

    Returns a list of dicts:
        [{"text": "...", "source": "runbooks/high_latency.md", "distance": 0.12}, ...]

    Distance is cosine distance (lower = more similar).
    """
    collection = get_collection()
    embedder = _get_embedder()

    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty — returning no results.")
        return []

    query_embedding = embedder.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "distance": round(dist, 4),
        })

    logger.debug(
        "semantic_retrieve(%r) → %d results: %s",
        query[:60],
        len(output),
        [r["source"] for r in output],
    )
    return output

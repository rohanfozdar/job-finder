import json
import os
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF
import faiss
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from candidate_profile import build_profile_text


# ==============================
# Module-level caches
# ==============================

_CACHED_MODEL = None
_CACHED_INDEX = None
_CACHED_CHUNKS = None


# ==============================
# Configuration helpers
# ==============================


def _get_project_root() -> Path:
    """
    Return the absolute path to the project root directory.

    This assumes that this file (vector_brain.py) lives in the project root.
    """
    return Path(__file__).resolve().parent


def _load_env() -> None:
    """
    Load environment variables from the .env file if present.
    """
    load_dotenv()


def _get_resume_path() -> Path:
    """
    Read RESUME_PATH from the environment and resolve it relative to
    the project root. Defaults to 'resume.pdf' if not set.
    """
    resume_name = os.getenv("RESUME_PATH", "resume.pdf")
    return _get_project_root() / resume_name


def _get_vector_store_dir() -> Path:
    """
    Read VECTOR_STORE_DIR from the environment and resolve it relative to
    the project root. Defaults to 'vector_store' if not set.
    """
    store_dir = os.getenv("VECTOR_STORE_DIR", "vector_store")
    return _get_project_root() / store_dir


# ==============================
# Resume loading and chunking
# ==============================


def load_resume_text(pdf_path: Path) -> str:
    """
    Extract all text from the given resume PDF using PyMuPDF.

    Returns a single long string containing the concatenated text of
    all pages.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Resume PDF not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    try:
        parts: List[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
    finally:
        doc.close()

    full_text = "\n".join(parts).strip()
    return full_text


def chunk_text(text: str, chunk_size_words: int = 300, overlap_words: int = 50) -> List[str]:
    """
    Split a long text into overlapping chunks of roughly `chunk_size_words`
    words with `overlap_words` shared between consecutive chunks.

    This is similar to highlighting a textbook in overlapping segments so
    no sentence loses all of its context at the boundaries.
    """
    if not text:
        return []

    words = text.split()
    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start = max(0, end - overlap_words)

    return chunks


# ==============================
# Embeddings and FAISS index
# ==============================


def embed_chunks(chunks: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Embed a list of text chunks into vectors using a local
    SentenceTransformer model.

    Returns a 2D NumPy array of shape (num_chunks, embedding_dim).
    """
    if not chunks:
        raise ValueError("No chunks provided to embed.")

    print(f"Embedding {len(chunks)} chunks...")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS IndexFlatIP index over the given embeddings.

    The vectors are normalized to unit length so that inner product
    corresponds to cosine similarity.
    """
    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a 2D array of shape (n, d).")

    num_vectors, dim = embeddings.shape
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS index built with {num_vectors} vectors of dim {dim}.")
    return index


def save_vector_store(index: faiss.IndexFlatIP, chunks: List[str], store_dir: Path) -> None:
    """
    Save the FAISS index and associated text chunks to disk.

    - Index is saved to:  profile.index
    - Chunks are saved as JSON list to: chunks.json
    """
    store_dir.mkdir(parents=True, exist_ok=True)
    index_path = store_dir / "profile.index"
    chunks_path = store_dir / "chunks.json"

    faiss.write_index(index, str(index_path))
    with chunks_path.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Vector store saved. {len(chunks)} chunks indexed.")
    print(f"Index path : {index_path}")
    print(f"Chunks path: {chunks_path}")


def load_vector_store(store_dir: Path) -> tuple[faiss.IndexFlatIP, List[str]]:
    """
    Load the FAISS index and chunk texts from disk.

    Returns a tuple of (index, chunks_list).
    """
    index_path = store_dir / "profile.index"
    chunks_path = store_dir / "chunks.json"

    if not index_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(
            f"Vector store not found in {store_dir}. "
            "Run this module as a script to build it first."
        )

    index = faiss.read_index(str(index_path))
    with chunks_path.open("r", encoding="utf-8") as f:
        chunks: List[str] = json.load(f)

    return index, chunks


# ==============================
# Query interface
# ==============================


def query_profile(job_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Query the saved vector store with a job description and return the
    top_k most similar chunks with their similarity scores.

    This will be called from the job-scoring phase to compute how well
    a job matches the resume + candidate profile.
    """
    if not job_text:
        raise ValueError("job_text must be a non-empty string.")

    global _CACHED_MODEL, _CACHED_INDEX, _CACHED_CHUNKS

    _load_env()
    store_dir = _get_vector_store_dir()

    if _CACHED_MODEL is None:
        _CACHED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    if _CACHED_INDEX is None:
        _CACHED_INDEX, _CACHED_CHUNKS = load_vector_store(store_dir)

    query_vec = _CACHED_MODEL.encode([job_text], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    scores, indices = _CACHED_INDEX.search(query_vec, top_k)
    scores = scores[0]
    indices = indices[0]

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores, indices):
        if 0 <= idx < len(_CACHED_CHUNKS):
            results.append({"chunk": _CACHED_CHUNKS[idx], "score": float(score)})

    return results


# ==============================
# Build pipeline
# ==============================


def build_vector_brain() -> None:
    """
    Run the end-to-end pipeline:
    - Load resume text from the configured PDF.
    - Chunk the resume into overlapping sections.
    - Load the candidate profile text and add it as an extra chunk.
    - Embed all chunks with SentenceTransformer.
    - Build and save the FAISS index plus raw chunks to disk.
    """
    _load_env()
    resume_path = _get_resume_path()
    store_dir = _get_vector_store_dir()

    print(f"Loading resume from: {resume_path}")
    resume_text = load_resume_text(resume_path)
    resume_chunks = chunk_text(resume_text, chunk_size_words=300, overlap_words=50)
    print(f"Resume split into {len(resume_chunks)} chunks.")

    profile_text = build_profile_text()
    print("Adding candidate profile text as an additional chunk.")

    all_chunks = resume_chunks + [profile_text]
    embeddings = embed_chunks(all_chunks, model_name="all-MiniLM-L6-v2")
    index = build_faiss_index(embeddings)
    save_vector_store(index, all_chunks, store_dir)


if __name__ == "__main__":
    build_vector_brain()

    # Self-test: query with a sample AI engineer intern description
    test_query = (
        "We are looking for an AI Engineer Intern with Python and deep learning experience."
    )
    print("\nRunning self-test query against the profile vector store...")
    top_results = query_profile(test_query, top_k=3)
    for i, res in enumerate(top_results, start=1):
        score = res["score"]
        snippet = res["chunk"][:200].replace("\n", " ")
        print(f"\n[{i}] score={score:.4f}")
        print(f"    {snippet}...")


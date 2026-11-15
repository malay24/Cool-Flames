"""Chunk investigation texts, embed, and index into data/ai/index/ (task A3).

Chunks come only from the PSI records' own text (objective, hypothesis,
approach, research impacts, description) plus a title line, about 500 tokens
each with ~50 tokens of overlap. Each chunk keeps psi_id, name and DOI so every
answer can cite its source.

Outputs (committed, so the deployed app never re-embeds):
    data/ai/index/chunks.json      chunk text + metadata
    data/ai/index/embeddings.npy   normalized float32 vectors (NumPy fallback)
    data/ai/index/faiss.index      inner-product FAISS index over the same vectors

Usage:
    python ai/build_index.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INDEX = ROOT / "data" / "ai" / "index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
FIELDS = [("objective", "Objective"), ("hypothesis", "Hypothesis"), ("approach", "Approach"),
          ("researchImpacts", "Research impacts"), ("description", "Description")]
CHUNK_WORDS = 380     # ~500 tokens
OVERLAP_WORDS = 40    # ~50 tokens


def record_chunks(record: dict) -> list[dict]:
    psi_id = record["accession"]
    name = (record.get("investigationAcronym") or "").strip() or record.get("title", psi_id)
    doi = record.get("doi", "")
    header = f"{name} ({psi_id}): {record.get('title', '')}."
    words: list[str] = []
    for key, label in FIELDS:
        text = " ".join((record.get(key) or "").split())
        if text:
            words += f"{label}: {text}".split()
    chunks = []
    step = CHUNK_WORDS - OVERLAP_WORDS
    for start in range(0, max(len(words), 1), step):
        piece = words[start:start + CHUNK_WORDS]
        if not piece:
            break
        chunks.append({"psi_id": psi_id, "name": name, "doi": doi,
                       "text": header + " " + " ".join(piece)})
        if start + CHUNK_WORDS >= len(words):
            break
    return chunks


def build_chunks() -> list[dict]:
    chunks: list[dict] = []
    for p in sorted(RAW.glob("PSI-*.json"), key=lambda x: int(x.stem.split("-")[1])):
        chunks += record_chunks(json.loads(p.read_text()))
    for i, c in enumerate(chunks):
        c["id"] = i
    return chunks


def main() -> int:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    chunks = build_chunks()
    model = SentenceTransformer(MODEL_NAME)
    vecs = model.encode([c["text"] for c in chunks], normalize_embeddings=True,
                        show_progress_bar=False).astype("float32")
    INDEX.mkdir(parents=True, exist_ok=True)
    (INDEX / "chunks.json").write_text(json.dumps(
        {"model": MODEL_NAME, "chunks": chunks}, indent=1, ensure_ascii=False) + "\n")
    np.save(INDEX / "embeddings.npy", vecs)
    try:
        import faiss
        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs)
        faiss.write_index(index, str(INDEX / "faiss.index"))
        faiss_note = "faiss.index written"
    except ImportError:
        faiss_note = "faiss not installed; NumPy search will be used"
    print(f"{len(chunks)} chunks from {len({c['psi_id'] for c in chunks})} investigations, "
          f"dim {vecs.shape[1]}; {faiss_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

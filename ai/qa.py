"""Retrieval + answer with DOI citations, with fallbacks (task A4).

answer(question) retrieves the top 5 chunks of PSI record text and:
  - with GEMINI_API_KEY + GEMINI_MODEL: asks Gemini to answer only from those
    chunks and cite DOIs (mode "gemini");
  - without a key, or if the API fails: returns the top passages with their
    DOIs (mode "passages").
Retrieval itself degrades: sentence-transformers + FAISS -> NumPy cosine ->
keyword overlap (if the embedding model cannot load). If the best match is
weak, the answer says the data does not cover the question.

Heavy imports (torch, sentence-transformers, faiss) happen lazily, never at
import time, so importing this module is cheap.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "ai" / "index"
TOP_K = 5
MIN_COSINE = 0.30      # below this the data likely does not cover the question
MIN_KEYWORD = 0.05
NO_COVERAGE = ("The PSI investigation texts in this app do not clearly cover this question. "
               "Try naming a fuel, a fire phase or an investigation (e.g. FLEX, SAME, Saffire).")

_STOP = set("""a an and are as at be by for from has have how in is it its of on or that the
their this to was were what when where which who why with does do did can could would should
about into than then there these those them they""".split())


@lru_cache(maxsize=1)
def load_chunks() -> tuple[str, list[dict]]:
    data = json.loads((INDEX / "chunks.json").read_text())
    return data["model"], data["chunks"]


@lru_cache(maxsize=1)
def _embedder():
    """(model, vectors, faiss_index or None). Raises ImportError if unavailable."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model_name, _ = load_chunks()
    model = SentenceTransformer(model_name)
    vecs = np.load(INDEX / "embeddings.npy")
    try:
        import faiss
        index = faiss.read_index(str(INDEX / "faiss.index"))
    except Exception:  # faiss missing or index unreadable -> NumPy search
        index = None
    return model, vecs, index


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower()) if t not in _STOP]


def _keyword_search(question: str, k: int) -> list[tuple[int, float]]:
    _, chunks = load_chunks()
    q = set(_tokens(question))
    if not q:
        return []
    docs = [Counter(_tokens(c["text"])) for c in chunks]
    df = Counter(t for d in docs for t in set(d))
    n = len(docs)
    scores = []
    for i, d in enumerate(docs):
        s = sum(math.log(1 + n / df[t]) * (1 + math.log(d[t])) for t in q if d[t])
        scores.append((i, s / (10 * len(q))))
    return sorted(scores, key=lambda x: -x[1])[:k]


KEYWORD_WEIGHT = 0.3  # hybrid: 70% embedding cosine + 30% normalized keyword score


def retrieve(question: str, k: int = TOP_K) -> tuple[list[dict], str]:
    """Top-k chunks with scores, and the retrieval method used.

    Semantic mode blends embedding cosine with keyword overlap (the small
    MiniLM model alone misses exact technical terms such as "cool flames").
    Each hit carries `score` (blended, used for ranking) and `cosine`.
    """
    _, chunks = load_chunks()
    n = len(chunks)
    try:
        model, vecs, index = _embedder()
        q = model.encode([question], normalize_embeddings=True).astype("float32")
        if index is not None:  # corpus is small: score every chunk
            scores, ids = index.search(q, n)
            cos = dict(zip(ids[0].tolist(), scores[0].tolist()))
            method = "faiss+keyword"
        else:
            sims = vecs @ q[0]
            cos = {i: float(sims[i]) for i in range(n)}
            method = "numpy+keyword"
    except ImportError:
        pairs = _keyword_search(question, k)
        return [{**chunks[i], "score": round(s, 3), "cosine": None} for i, s in pairs], "keyword"

    kw = dict(_keyword_search(question, n))
    kw_max = max(kw.values(), default=0.0) or 1.0
    blended = {i: (1 - KEYWORD_WEIGHT) * cos.get(i, 0.0) + KEYWORD_WEIGHT * kw.get(i, 0.0) / kw_max
               for i in range(n)}
    top = sorted(blended, key=lambda i: -blended[i])[:k]
    return [{**chunks[i], "score": round(blended[i], 3), "cosine": round(cos.get(i, 0.0), 3)}
            for i in top], method


def _citations(hits: list[dict]) -> list[dict]:
    seen, out = set(), []
    for h in hits:
        if h["psi_id"] not in seen:
            seen.add(h["psi_id"])
            out.append({"psi_id": h["psi_id"], "name": h["name"], "doi": h["doi"]})
    return out


def _prompt(question: str, hits: list[dict]) -> str:
    sources = "\n\n".join(f"[{n}] {h['name']} ({h['psi_id']}), DOI {h['doi']}:\n{h['text']}"
                          for n, h in enumerate(hits, 1))
    return (
        "You answer questions about NASA microgravity combustion investigations for a research "
        "dashboard. Use ONLY the sources below. If they do not answer the question, say so. "
        "Cite every claim with the source's DOI in brackets, e.g. [10.60555/mbq8-0451]. "
        "Do not invent numbers. Never describe anything as 'safe', 'approved' or 'will not "
        "burn'; say 'tests show' or 'no data'. Answer in at most 6 sentences.\n\n"
        f"Sources:\n{sources}\n\nQuestion: {question}\nAnswer:"
    )


def answer(question: str) -> dict:
    """{answer, citations, passages, mode, retrieval, note}."""
    question = (question or "").strip()
    if not question:
        return {"answer": "Ask a question about the investigations.", "citations": [],
                "passages": [], "mode": "none", "retrieval": "", "note": ""}
    hits, method = retrieve(question)
    if method == "keyword":
        best, floor = (hits[0]["score"] if hits else 0.0), MIN_KEYWORD
    else:
        best, floor = max((h["cosine"] for h in hits), default=0.0), MIN_COSINE
    if not hits or best < floor:
        return {"answer": NO_COVERAGE, "citations": [], "passages": hits[:3],
                "mode": "no_coverage", "retrieval": method, "note": f"best match {best:.2f}"}

    from ai.llm import LLMUnavailable, call_llm_text, has_key

    note = ""
    if has_key():
        try:
            text = call_llm_text(_prompt(question, hits)).strip()
            if text:
                return {"answer": text, "citations": _citations(hits), "passages": hits,
                        "mode": "gemini", "retrieval": method, "note": ""}
        except LLMUnavailable as exc:
            note = f"Gemini unavailable ({str(exc)[:120]}); showing the source passages instead."
    else:
        note = "No Gemini key configured; showing the most relevant source passages."
    summary = "Most relevant passages from the PSI investigation records:"
    return {"answer": summary, "citations": _citations(hits), "passages": hits,
            "mode": "passages", "retrieval": method, "note": note}

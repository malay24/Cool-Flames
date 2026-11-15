"""Q&A retrieval and no-key fallback (tasks A3/A4)."""
import pytest

from ai import qa


@pytest.fixture(autouse=True)
def no_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr("ai.llm.has_key", lambda: False)


def test_index_chunks_carry_dois():
    _, chunks = qa.load_chunks()
    assert len(chunks) >= 24
    assert all(c["doi"].startswith("10.") and c["psi_id"].startswith("PSI-") for c in chunks)


def test_keyword_search_finds_smoke_studies():
    _, chunks = qa.load_chunks()
    top = [chunks[i]["psi_id"] for i, _ in qa._keyword_search("smoke particle detector Kapton", 3)]
    assert {"PSI-101", "PSI-102"} & set(top)


def test_answer_without_key_returns_passages_with_dois():
    r = qa.answer("Which materials did the ISS smoke detector struggle with?")
    assert r["mode"] == "passages"
    assert r["citations"] and all(c["doi"] for c in r["citations"])
    assert {"PSI-101", "PSI-102"} & {c["psi_id"] for c in r["citations"]}


def test_off_topic_question_is_not_answered():
    assert qa.answer("What is the price of bitcoin?")["mode"] == "no_coverage"

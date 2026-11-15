"""Ask (stretch): questions answered only from PSI investigation texts, citing DOIs.

Task P8. Uses ai/qa.py. With a Google AI Studio key (GEMINI_API_KEY and
GEMINI_MODEL in .env or Streamlit secrets) Gemini writes a cited answer;
without one, the page shows the most relevant source passages with DOIs.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import streamlit as st  # noqa: E402

from components import doi_link, footer, page_header  # noqa: E402

page_header("Tools · Ask", "Ask the investigations",
            "Answers come only from the text of the 24 NASA PSI combustion records, and every "
            "answer links the DOIs it used. Research tool, not an operational safety system.")

# Streamlit Cloud secrets -> environment, so ai/llm.py finds the key.
for key in ("GEMINI_API_KEY", "GEMINI_MODEL"):
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
    except Exception:  # no secrets file locally
        pass

try:
    from ai import qa
except Exception as exc:  # an install problem should only affect this page
    st.error(f"The Ask feature is unavailable on this deployment ({exc}).")
    footer()
    st.stop()


@st.cache_resource(show_spinner="Loading the search index…")
def _warm() -> bool:
    qa.load_chunks()
    try:
        qa._embedder()
        return True
    except ImportError:
        return False


semantic = _warm()
if not semantic:
    st.info("Semantic search is unavailable here, so answers use keyword matching.", icon=":material/info:")

EXAMPLES = ["Which materials did the ISS smoke detector struggle with?",
            "What are cool flames and where were they seen?",
            "How was large-scale fire growth studied without risking a crew?",
            "Which experiments tested oxygen-enriched atmospheres?"]
st.session_state.setdefault("ask_history", [])



def _pick_example() -> None:
    st.session_state["ask_pending"] = st.session_state.get("ask_examples")
    st.session_state["ask_examples"] = None  # clear so a rerun does not ask again


st.pills("Try an example", EXAMPLES, key="ask_examples", selection_mode="single",
         on_change=_pick_example)
picked = st.session_state.pop("ask_pending", None)


def show(result: dict) -> None:
    st.markdown(result["answer"])
    if result.get("note"):
        st.caption(result["note"])
    if result["mode"] == "passages":
        for p in result["passages"]:
            with st.container(border=True):
                st.markdown(f"**{p['name']}** · `{p['psi_id']}` · match {p['score']:.2f}")
                st.markdown(p["text"][:900] + ("…" if len(p["text"]) > 900 else ""))
                st.markdown(doi_link(p["doi"]))
    if result.get("citations"):
        st.markdown("**Sources:** " + " · ".join(f"{c['name']} {doi_link(c['doi'])}"
                                                 for c in result["citations"]))


for turn in st.session_state["ask_history"]:
    with st.chat_message("user"):
        st.markdown(turn["q"])
    with st.chat_message("assistant"):
        show(turn["r"])

question = st.chat_input("Ask about fuels, oxygen levels, smoke, suppression…") or picked
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching the investigation texts…"):
            result = qa.answer(question)
        show(result)
    st.session_state["ask_history"].append({"q": question, "r": result})

footer()

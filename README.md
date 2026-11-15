# Cool Flames — Fire Scenario Explorer

NASA Space Apps Challenge 2026 — "Flame in Freefall: SI-Powered Fire Safety
Insights from Microgravity Combustion Data".

A web dashboard that summarizes, ranks and interprets NASA's microgravity
combustion investigations (NASA Physical Sciences Informatics, CC0) to deliver
fire-safety insights for crewed exploration. Pick a habitat and a fire scenario;
the app ranks the investigations that matter for each phase of that fire, shows
how close tested conditions come to the habitat's atmosphere, and flags where no
data exists.

> **Research and reference tool, not an operational safety system.** Data: NASA
> PSI (CC0). See CLAUDE.md for the full brief and SCHEMA.md for the data contract.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/Home.py
```

The deployed app runs with no API key (all LLM outputs are generated offline and
committed). The Ask page degrades to keyword search if the API is unavailable.

## Layout

- `core/` — pure ranking and scenario logic (no Streamlit).
- `pipeline/` — offline data build (`data/raw/` -> `data/clean/`).
- `ai/` — offline AI build (tags, summaries, Q&A index) + Q&A.
- `app/` — Streamlit multipage app.
- `data/` — `raw/`, `clean/`, `ai/`, `manual/`, `fake/`.

## Data sources and AI use

TODO (S3/S6): list every investigation with its DOI and declare AI use.

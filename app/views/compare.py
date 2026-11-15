"""Compare (stretch): 2 to 4 investigations side by side. Task P7.

Fuels, conditions, hardware, what varied between runs, outcomes and the main
metric, all computed from investigations.json and the standardized tests.csv.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from components import (demo_badge, doi_link, dossier_link, fmt_range, footer,  # noqa: E402
                        page_header)
from components.data import load_investigations, load_tests  # noqa: E402

page_header("Tools · Compare", "Compare investigations side by side",
            "Pick 2 to 4 studies to compare fuels, tested conditions, what varied between runs and "
            "what was measured.")
invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
demo_badge(inv_demo or tests_demo)
by_id = {i["psi_id"]: i for i in invs}

ids = sorted(by_id, key=lambda p: int(p.split("-")[1]))
default = [p for p in ("PSI-101", "PSI-102", "PSI-69") if p in by_id] or ids[:2]
picked = st.multiselect("Pick 2 to 4 investigations", ids, default=default, max_selections=4,
                        format_func=lambda p: f"{by_id[p]['name']} ({p})")
if len(picked) < 2:
    st.info("Pick at least two investigations to compare.")
    st.stop()

VARIED_COLS = {"fuel": "fuel", "o2_pct": "O₂", "pressure_psi": "pressure", "diluent": "diluent",
               "airflow_cms": "airflow", "sample_size_mm": "sample size"}


def describe(psi_id: str) -> dict:
    inv = by_id[psi_id]
    runs = tests[tests["psi_id"] == psi_id]
    fuels = inv.get("fuels") or list(runs["fuel"].dropna().astype(str).value_counts().index[:5])
    varied = [label for col, label in VARIED_COLS.items()
              if col in runs and runs[col].dropna().nunique() > 1]
    outcomes = runs["outcome"].dropna().value_counts()
    metric = "not tabulated"
    m = runs.dropna(subset=["metric_value"])
    if not m.empty:
        name, unit = m["metric_name"].iloc[0], m["metric_unit"].iloc[0]
        metric = (f"{name.replace('_', ' ')}: {m['metric_value'].min():g}–"
                  f"{m['metric_value'].max():g} {unit} ({len(m)} runs)")
    diluents = ", ".join(sorted(runs["diluent"].dropna().astype(str).unique())) or "not reported"
    return {
        "Fire-safety area": inv.get("area", ""),
        "Platform": inv.get("platform") or "not listed",
        "Hardware": inv.get("hardware") or "not listed",
        "Test scale": inv.get("test_scale", ""),
        "Fuel phase": ", ".join(inv.get("fuel_types") or []) or "none",
        "Fuels / materials": ", ".join(fuels) or "not listed",
        "Test runs (PSI table)": str(inv.get("n_runs") or "text only"),
        "Runs standardized": str(len(runs)),
        "O₂": fmt_range(inv.get("o2_range"), "%"),
        "Pressure": fmt_range(inv.get("pressure_range"), "psi"),
        "Airflow": fmt_range(inv.get("airflow_range"), "cm/s"),
        "Sample size": fmt_range(inv.get("sample_size_range"), "mm"),
        "Diluent": diluents,
        "What varied between runs": ", ".join(varied) or "nothing tabulated",
        "Outcomes": ", ".join(f"{k} {v}" for k, v in outcomes.items()) or "not reported",
        "Main measurement": metric,
        "Publications": str(inv.get("n_publications", 0)),
        "DOI": inv.get("doi", ""),
    }


table = pd.DataFrame({by_id[p]["name"]: describe(p) for p in picked})
st.dataframe(table, width="stretch", height=(len(table) + 1) * 36)

# ---- similarities and differences ----
st.subheader("Similarities and differences")
notes = []
areas = {by_id[p]["area"] for p in picked}
notes.append(f"All in the **{areas.pop()}** area." if len(areas) == 1
             else f"Different areas: {', '.join(sorted(areas | {by_id[picked[0]]['area']}))}.")
phases = [set(by_id[p].get("fuel_types") or []) for p in picked]
shared = set.intersection(*phases)
notes.append(f"Shared fuel phase: **{', '.join(sorted(shared))}**." if shared
             else "No fuel phase in common.")
o2 = [by_id[p].get("o2_range") for p in picked]
if all(o2):
    lo, hi = max(r[0] for r in o2), min(r[1] for r in o2)
    notes.append(f"O₂ ranges overlap at **{lo:g}–{hi:g}%**." if lo <= hi
                 else "O₂ ranges do not overlap.")
else:
    missing = [by_id[p]["name"] for p, r in zip(picked, o2) if not r]
    notes.append(f"O₂ not reported for: {', '.join(missing)}, so conditions cannot be compared fully.")
for n in notes:
    st.markdown(f"- {n}")

st.markdown("**Cite:** " + " · ".join(f"{by_id[p]['name']} {doi_link(by_id[p]['doi'])}"
                                       for p in picked))
for col, p in zip(st.columns(len(picked)), picked):
    with col:
        dossier_link(p, f"{by_id[p]['name']} dossier")
footer()

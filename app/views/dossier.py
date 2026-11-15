"""Study dossier: one investigation on one page.

Covers what the brief asks for each investigation: objectives, fuel, sample
shape and size, conditions, what varied, sensors and measurements, and similar
studies. Record text and table columns are shown verbatim from data/raw/; the
summary is the AI-written one from investigations.json. Open with ?id=PSI-99.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from ai.dossier import ATTR_WEIGHTS, TEXT_WEIGHT, instruments, people, record_sections  # noqa: E402
from components import (area_badge, chips, current_habitat, demo_badge, doi_link,  # noqa: E402
                        dossier_link, fmt_range, footer, is_dark, page_header, stat_row, tokens)
from components.data import (habitats, load_investigations, load_raw_tables,  # noqa: E402
                             load_record, load_similar, load_table_profile, load_tests)
from core.ranking import condition_overlap  # noqa: E402

invs, inv_demo = load_investigations()
tests, tests_demo = load_tests()
by_id = {i["psi_id"]: i for i in invs}
ids = sorted(by_id, key=lambda p: int(re.sub(r"\D", "", p) or 0))

# ---- which investigation: ?id= in the URL, kept in step with the picker ----
asked = st.query_params.get("id")
last = st.session_state.get("_dossier_url")  # survives page changes; widget state does not
if asked in by_id and (asked != last or "dossier_pick" not in st.session_state):
    st.session_state["dossier_pick"] = asked
if st.session_state.get("dossier_pick") not in by_id:
    st.session_state["dossier_pick"] = last if last in by_id else ("PSI-99" if "PSI-99" in by_id else ids[0])

page_header("Explore · Study dossier", "Everything about one investigation",
            "Objectives, fuels and samples, tested conditions, what varied, what was measured and "
            "with which instruments, plus the closest related studies. Text from the NASA record is "
            "quoted as written.")
demo_badge(inv_demo or tests_demo)
pid = st.selectbox("Investigation", ids, key="dossier_pick",
                   format_func=lambda p: f"{by_id[p]['name']} ({p})")
st.query_params["id"] = pid
st.session_state["_dossier_url"] = pid

inv = by_id[pid]
record = load_record(pid)
profile = load_table_profile(pid)
runs = tests[tests["psi_id"] == pid]
habs = habitats()
hab = habs[current_habitat()]

# ---- identity ----
with st.container(border=True):
    st.markdown(f"### {inv['name']}")
    st.markdown(f"{area_badge(inv['area'])} &nbsp; `{pid}` &nbsp; {doi_link(inv.get('doi', ''))}")
    if inv.get("title") and inv.get("title") != inv.get("name"):
        st.caption(inv["title"])
    dates = " – ".join(d for d in (inv.get("start_date"), inv.get("end_date")) if d)
    facts = [("Platform", inv.get("platform") or "ground study"),
             ("Hardware", inv.get("hardware") or "not listed")]
    if dates:
        facts.append(("Dates", dates))
    if record.get("managingNasaCenter"):
        facts.append(("NASA center", record["managingNasaCenter"]))
    if record.get("subResearchArea"):
        facts.append(("Topic", record["subResearchArea"]))
    st.html(chips(facts))
    team = people(record)
    if team:
        st.caption(("Principal investigator" + ("s" if len(team) > 1 else "")) + ": " + "; ".join(team))

n_runs, n_std = inv.get("n_runs") or 0, len(runs)
stat_row([("Test runs (NASA table)", f"{n_runs:,}" if n_runs else "text only"),
          ("Runs standardized", f"{n_std:,}", "Rows in tests.csv used by the ranking and gap map."),
          ("Publications", inv.get("n_publications", 0)),
          ("Test scale", (inv.get("test_scale") or "–").replace("_", " "))])

# ---- summary + habitat fit ----
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("Summary", anchor=False)
    st.caption("AI-written from this record's own text; check it against the quotes below.")
    if inv.get("summary_3line"):
        st.markdown(inv["summary_3line"].replace("\n", "  \n"))
    for kf in inv.get("key_findings") or []:
        st.markdown(f"- {kf}")
with right:
    st.subheader("Against your habitat", anchor=False)
    st.caption(f"{hab['label']}: {hab['o2_pct']:g}% O₂ at {hab['pressure_psi']:g} psi "
               "(change it in the sidebar).")
    _, nearest = condition_overlap(runs, hab)
    if nearest:
        d = nearest["distance"]
        verdict = ("close to this atmosphere" if d <= 0.1 else
                   "some distance from it" if d <= 0.5 else "far from it")
        box = st.success if d <= 0.1 else st.info if d <= 0.5 else st.warning
        box(f"Closest tested run: **{nearest['o2_pct']:g}% O₂ at {nearest['pressure_psi']:g} psi** "
            f"(normalized distance {d:.2f}, {verdict}). The gap map counts runs within 0.1 as nearby.",
            icon=":material/my_location:")
    else:
        st.info("This study does not report O₂ and pressure together, so it cannot be placed "
                "against a habitat atmosphere.", icon=":material/help:")
    if hab.get("partial_gravity"):
        st.warning("**No data yet: partial gravity.** No PSI study tested Moon or Mars gravity; "
                   "these results come from microgravity (or ground) tests.", icon=":material/public:")

# ---- the NASA record, verbatim ----
sections = record_sections(record)
if sections:
    st.subheader("From the NASA record", anchor=False)
    st.caption("Quoted as written in the PSI record.")
    for tab, (label, text) in zip(st.tabs([s[0] for s in sections]), sections):
        tab.markdown(f"> {text}")

# ---- what was tested ----
st.subheader("What was tested", anchor=False)
by_cat = {c: [p for p in profile if p["category"] == c] for c in ("sample", "condition", "measured")}
multi_table = len({p["table"] for p in profile}) > 1
varied = [p["column"] for p in profile if p["varied"] and p["category"] in ("sample", "condition")]
if varied:
    st.markdown("**Varied between runs** (sample and condition columns of the NASA table with more "
                "than one value): " + ", ".join(dict.fromkeys(varied)))
elif profile:
    st.markdown("**Varied between runs:** no sample or condition column changes between runs.")
elif not profile:
    st.caption("No experiment table in PSI for this investigation (text only).")


def column_lines(items: list[dict]) -> None:
    for p in items:
        more = p["n_values"] - len(p["examples"])
        ex = " · ".join(p["examples"]) + (f" (+{more} more)" if more > 0 else "")
        tag = f" _({p['table']})_" if multi_table else ""
        flag = " :orange-badge[varied]" if p["varied"] else ""
        st.markdown(f"- **{p['column']}**{tag}{flag}  \n  {ex}")


c1, c2, c3 = st.columns(3, gap="medium")
with c1.container(border=True):
    st.markdown("#### :material/category: Sample and fuel")
    fuels = runs["fuel"].dropna().astype(str).value_counts()
    if not fuels.empty:
        st.markdown("Fuels in the standardized runs: " + ", ".join(
            f"{f} ({n})" for f, n in fuels.head(6).items()) + (" …" if len(fuels) > 6 else ""))
    elif inv.get("fuels"):
        st.markdown("Fuels: " + ", ".join(inv["fuels"]))
    st.html(chips([("Fuel phase", ", ".join(inv.get("fuel_types") or []) or "none"),
                   ("Sample size", fmt_range(inv.get("sample_size_range"), "mm"))]))
    if by_cat["sample"]:
        column_lines(by_cat["sample"])
    else:
        st.caption("No sample columns in the table.")

with c2.container(border=True):
    st.markdown("#### :material/tune: Conditions")
    dil = ", ".join(sorted(runs["diluent"].dropna().astype(str).unique())) or "not reported"
    ppo2 = runs["ppo2_psi"].dropna()
    st.html(chips([("O₂", fmt_range(inv.get("o2_range"), "%")),
                   ("Pressure", fmt_range(inv.get("pressure_range"), "psi"))]) + "<br>" + chips([
        ("ppO₂", fmt_range([round(ppo2.min(), 2), round(ppo2.max(), 2)], "psi") if len(ppo2) else "not reported"),
        ("Airflow", fmt_range(inv.get("airflow_range"), "cm/s")), ("Diluent", dil)]))
    if by_cat["condition"]:
        column_lines(by_cat["condition"])
    else:
        st.caption("No condition columns in the table.")

with c3.container(border=True):
    st.markdown("#### :material/sensors: Measurements and instruments")
    m = runs.dropna(subset=["metric_value"])
    if not m.empty:
        name, unit = m["metric_name"].iloc[0].replace("_", " "), m["metric_unit"].iloc[0]
        st.markdown(f"Main measurement: **{name}**, {m['metric_value'].min():g}–"
                    f"{m['metric_value'].max():g} {unit} ({len(m)} runs)")
    outcomes = runs["outcome"].dropna().value_counts()
    outcomes = outcomes[outcomes.index != "unknown"]
    if not outcomes.empty:
        st.markdown("Outcomes: " + ", ".join(f"{k} {v}" for k, v in outcomes.items()))
    if by_cat["measured"]:
        column_lines(by_cat["measured"])
    else:
        st.caption("No result columns in the table.")
    found = instruments(record, profile)
    if found:
        st.markdown("**Instruments named in the record:** " + ", ".join(i["label"] for i in found))
        with st.expander("Where the record names them"):
            for i in found:
                st.markdown(f"**{i['label']}** · {i['where']}  \n> {i['quote']}")
    else:
        st.caption("The record text names no instruments; see the publications.")

# ---- runs chart (dataviz reference palette, validated light + dark) ----
FIELDS = {"metric_value": None, "o2_pct": "O₂ (%)", "pressure_psi": "Total pressure (psi)",
          "ppo2_psi": "O₂ partial pressure (psi)", "airflow_cms": "Airflow (cm/s)",
          "sample_size_mm": "Sample size (mm)"}
if not m.empty:
    FIELDS["metric_value"] = f"{m['metric_name'].iloc[0].replace('_', ' ').capitalize()} ({m['metric_unit'].iloc[0]})"
MIN_POINTS = 5  # fewer values than this: the table says more than a chart would
avail = [c for c, label in FIELDS.items()
         if label and runs[c].dropna().nunique() > 1 and runs[c].notna().sum() >= MIN_POINTS]
if len(avail) >= 2:
    st.subheader("Explore the runs", anchor=False)
    y_default = "metric_value" if "metric_value" in avail else "o2_pct" if "o2_pct" in avail else avail[0]
    x_pref = [c for c in ("pressure_psi", "o2_pct", "airflow_cms", "sample_size_mm", "ppo2_psi")
              if c in avail and c != y_default]
    a, b = st.columns(2)
    y = a.selectbox("Vertical axis", avail, index=avail.index(y_default), key=f"dy_{pid}",
                    format_func=lambda c: FIELDS[c])
    x_opts = [c for c in avail if c != y]
    x = b.selectbox("Horizontal axis", x_opts, key=f"dx_{pid}", format_func=lambda c: FIELDS[c],
                    index=x_opts.index(x_pref[0]) if x_pref and x_pref[0] in x_opts else 0)
    pts = runs.dropna(subset=[x, y]).copy()

    DARK, T = is_dark(), tokens()
    INK = {"primary": T["text"], "secondary": T["muted"], "grid": T["grid"], "axis": T["axis"],
           "surface": T["bg"]}
    SLOTS = (["#3987e5", "#d95926", "#199e70", "#c98500"] if DARK
             else ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"])
    SYMBOLS = ["circle", "diamond", "square", "triangle-up", "x"]
    fuel = pts["fuel"].fillna("fuel not reported").astype(str)  # blank stays visible, not "Other"
    top = list(fuel.value_counts().index[:4])
    pts["group"] = fuel.where(fuel.isin(top), "Other")
    groups = top + (["Other"] if (pts["group"] == "Other").any() else [])

    fig = go.Figure()
    for n, g in enumerate(groups):
        sub = pts[pts["group"] == g]
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], mode="markers", name=g,
            marker=dict(color=SLOTS[n] if n < 4 else "#898781", symbol=SYMBOLS[n], size=9,
                        opacity=0.85, line=dict(color=INK["surface"], width=2)),
            customdata=sub[["run_id", "outcome"]].astype(str).values,
            hovertemplate=(f"<b>{g}</b> · run %{{customdata[0]}}<br>{FIELDS[x]}: %{{x:.3g}}<br>"
                           f"{FIELDS[y]}: %{{y:.3g}}<br>outcome: %{{customdata[1]}}<extra></extra>")))
    if {x, y} == {"o2_pct", "pressure_psi"}:
        hx, hy = hab[x], hab[y]
        fig.add_trace(go.Scatter(x=[hx], y=[hy], mode="markers+text", name=hab["label"],
                                 text=[hab["label"].split(" /")[0]], textposition="top center",
                                 textfont=dict(color=INK["primary"]),
                                 marker=dict(symbol="star", size=18, color=INK["primary"],
                                             line=dict(color=INK["surface"], width=2)),
                                 hovertemplate=f"<b>{hab['label']}</b><extra></extra>"))
    axis = dict(gridcolor=INK["grid"], linecolor=INK["axis"], zeroline=False, automargin=True,
                tickfont=dict(color=INK["secondary"]), title_font=dict(color=INK["secondary"]))
    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=36, b=10), showlegend=len(fig.data) > 1,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif", color=INK["primary"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=INK["secondary"])),
        hoverlabel=dict(bgcolor=T["panel"], font_color=INK["primary"]),
        xaxis=dict(title=FIELDS[x], **axis), yaxis=dict(title=FIELDS[y], **axis))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(f"{len(pts)} of {len(runs)} standardized runs have both values. Blank cells are "
               "left out, never set to 0. Colour and shape mark the fuel; the table below has every value.")

# ---- similar studies ----
st.subheader("Similar studies", anchor=False)
st.caption(f"Score = {TEXT_WEIGHT:.0%} similarity of the record text (MiniLM embeddings from the Ask "
           f"index) + {1 - TEXT_WEIGHT:.0%} shared attributes (area {ATTR_WEIGHTS['area']:.0%}, fuel "
           f"phase {ATTR_WEIGHTS['phase']:.0%}, hardware {ATTR_WEIGHTS['hardware']:.0%}, O₂ overlap "
           f"{ATTR_WEIGHTS['o2']:.0%}).")
similar = load_similar(pid)
if similar:
    for col, s in zip(st.columns(len(similar)), similar):
        with col.container(border=True):
            st.markdown(f"**{s['name']}**  \n{area_badge(s['area'])} &nbsp; `{s['psi_id']}`")
            st.progress(min(1.0, s["score"]), text=f"Similarity {s['score']:.2f}")
            reasons = s["reasons"] + [f"text similarity {s['text_similarity']:.2f}"]
            st.caption(" · ".join(reasons))
            dossier_link(s["psi_id"])
else:
    st.caption("No other investigations to compare with.")

# ---- publications and data ----
pubs = inv.get("publications") or []
if pubs:
    with st.expander(f"Publications ({len(pubs)})", icon=":material/menu_book:"):
        for p in pubs:
            link = f" · [doi:{p['doi']}](https://doi.org/{p['doi']})" if p.get("doi") else ""
            authors = f" {p['authors']}." if p.get("authors") else ""
            st.markdown(f"- **{p.get('title', 'Untitled')}**.{authors}{link}")

if not runs.empty:
    with st.expander(f"Standardized runs ({len(runs)})", icon=":material/table_chart:"):
        st.dataframe(runs.drop(columns=["psi_id"]), width="stretch", hide_index=True)
        st.download_button("Download these runs (CSV)", runs.to_csv(index=False).encode(),
                           file_name=f"{pid}_runs.csv", mime="text/csv", icon=":material/download:")
for name, frame in load_raw_tables(pid):
    with st.expander(f"Raw NASA table: {name} ({len(frame)} rows)", icon=":material/dataset:"):
        st.caption("As published in PSI, blank rows removed. Use it to check any value above.")
        st.dataframe(frame, width="stretch", hide_index=True)

st.markdown(f"**Cite:** {inv['name']}, NASA Physical Sciences Informatics, {doi_link(inv.get('doi', ''))}")
footer()

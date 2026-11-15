"""Gap map: every test run on pressure vs O2 %, habitats on top, iso-ppO2 curves.

Tasks P4 (chart) and P6 (CSV download). CLAUDE.md section 9.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # app/, for `components`

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from components import (current_habitat, demo_badge, footer, is_dark, page_header,  # noqa: E402
                        stat_row, tokens)
from components.data import habitats, load_investigations, load_tests  # noqa: E402
from core import loaders  # noqa: E402

habitat_key = current_habitat()
page_header("Explore · Gap map", "Where has NASA actually tested?",
            "Every standardized test run by total pressure and oxygen fraction, with the habitat "
            "atmospheres on top. Empty space is where no data exists.")

tests, tests_demo = load_tests()
invs, inv_demo = load_investigations()
demo_badge(tests_demo or inv_demo)
inv_by_id = {i["psi_id"]: i for i in invs}
HABS = habitats()

# ---- palette (dataviz reference palette; validated light + dark) ----
DARK = is_dark()
T = tokens()  # page theme (see .streamlit/config.toml)
INK = {"primary": T["text"], "secondary": T["muted"], "muted": "#8a93a6" if DARK else "#7b7f87",
       "grid": T["grid"], "axis": T["axis"], "surface": T["bg"]}
# Fixed area -> style, so a colour always means the same area (never by rank).
AREA_STYLE = {
    "suppression": ("#3987e5" if DARK else "#2a78d6", "circle"),
    "basic": ("#199e70" if DARK else "#1baf7a", "square"),
    "prevention": ("#d95926" if DARK else "#eb6834", "diamond"),
    "detection": ("#9085e9" if DARK else "#6250d6", "triangle-up"),
    "modelling": ("#898781", "x"),
}
# psi: exploration habitat, ISS / Moon brief, spacesuit (CLAUDE.md section 9)
PPO2_LINES = [(2.8, "dot"), (3.1, "dash"), (4.3, "longdash")]
# Leader-line offsets (pixels) pointing each habitat label into empty plot space.
LABEL_OFFSETS = {"suit": (70, 10), "exploration": (-30, -75), "moon_brief": (120, -70),
                 "iss": (80, 45)}

# ---- data ----
df = tests.copy()
df["area"] = df["psi_id"].map(lambda p: inv_by_id.get(p, {}).get("area", "basic"))
df["name"] = df["psi_id"].map(lambda p: inv_by_id.get(p, {}).get("name", p))
df["doi"] = df["psi_id"].map(lambda p: inv_by_id.get(p, {}).get("doi", ""))
plot = df.dropna(subset=["o2_pct", "pressure_psi"]).copy()
plot["ppo2"] = plot["o2_pct"] / 100 * plot["pressure_psi"]
plot["flagged"] = ~plot["ppo2"].between(0.5, 16)

h = HABS[habitat_key]
dist = (((plot["o2_pct"] - h["o2_pct"]) / 100) ** 2
        + ((plot["pressure_psi"] - h["pressure_psi"]) / 14.7) ** 2) ** 0.5
near = plot[dist <= 0.1]

stat_row([
    ("Runs plotted", f"{len(plot):,} of {len(df):,}", "Runs with both O₂ and pressure reported."),
    ("Investigations plotted", plot["psi_id"].nunique()),
    (f"Runs near {h['label'].split(' /')[0]}", len(near),
     "Within 0.1 in normalized distance: about 10 O₂ points or 1.5 psi."),
])

# ---- figure ----
fig = go.Figure()
for area, (color, symbol) in AREA_STYLE.items():
    sub = plot[plot["area"] == area]
    if sub.empty:
        continue
    fig.add_trace(go.Scatter(
        x=sub["pressure_psi"], y=sub["o2_pct"], mode="markers", name=area,
        marker=dict(color=color, symbol=symbol, size=8, opacity=0.85,
                    line=dict(color=INK["surface"], width=1)),
        customdata=sub[["name", "psi_id", "run_id", "fuel", "doi", "ppo2", "outcome"]]
        .fillna("").values,
        hovertemplate=("<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                       "run %{customdata[2]} · %{customdata[3]}<br>"
                       "%{y:.1f}% O₂ · %{x:.1f} psi · ppO₂ %{customdata[5]:.2f} psi<br>"
                       "outcome: %{customdata[6]}<br>doi:%{customdata[4]}<extra></extra>"),
    ))

# Iso-ppO2 curves: identified by dash pattern + legend entry (no labels to collide).
p_curve = [p / 4 for p in range(8, 4 * 76)]
for pp, dash in PPO2_LINES:
    xs = [p for p in p_curve if 100 * pp / p <= 100]
    fig.add_trace(go.Scatter(
        x=xs, y=[100 * pp / p for p in xs], mode="lines", hoverinfo="skip",
        name=f"ppO₂ {pp:g} psi", legendgroup="ppo2",
        line=dict(color=INK["muted"], width=1.5, dash=dash),
    ))

# Habitat stars; labels are annotations with a surface-coloured box and a leader
# line into empty space, so they stay legible over the data.
for key, hab in HABS.items():
    sel = key == habitat_key
    fig.add_trace(go.Scatter(
        x=[hab["pressure_psi"]], y=[hab["o2_pct"]], mode="markers", showlegend=False,
        marker=dict(symbol="star", size=22 if sel else 15, color=INK["primary"],
                    line=dict(color=INK["surface"], width=2)),
        hovertemplate=(f"<b>{hab['label']}</b><br>{hab['o2_pct']:g}% O₂ · "
                       f"{hab['pressure_psi']:g} psi · ppO₂ {hab['ppo2_psi']:.2f} psi<extra></extra>"),
    ))
    ax, ay = LABEL_OFFSETS.get(key, (60, -30))
    fig.add_annotation(
        x=hab["pressure_psi"], y=hab["o2_pct"], ax=ax, ay=ay,
        text=f"<b>{hab['label']}</b>" if sel else hab["label"],
        showarrow=True, arrowhead=0, arrowwidth=1, arrowcolor=INK["secondary"],
        bgcolor=INK["surface"], opacity=0.92, borderpad=3,
        font=dict(color=INK["primary"] if sel else INK["secondary"], size=13 if sel else 12),
    )

axis = dict(gridcolor=INK["grid"], linecolor=INK["axis"], zeroline=False, automargin=True,
            tickfont=dict(color=INK["secondary"]), title_font=dict(color=INK["secondary"]))
fig.update_layout(
    height=600, margin=dict(l=70, r=20, t=50, b=60),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif", color=INK["primary"]),
    xaxis=dict(title="Total pressure (psi)", range=[0, 76], **axis),
    yaxis=dict(title="O₂ (% by volume)", range=[0, 105], **axis),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, title_text="",
                font=dict(color=INK["secondary"])),
    hoverlabel=dict(bgcolor=T["panel"], font_color=INK["primary"]),
)
st.plotly_chart(fig, width="stretch", theme=None)

# ---- reading notes ----
by_inv = plot.groupby("name").size().sort_values(ascending=False)
st.caption(
    f"{len(plot):,} of {len(df):,} standardized runs plotted ("
    + ", ".join(f"{n} {k}" for k, n in by_inv.items())
    + "). Runs without both O₂ and pressure reported are omitted, not assumed to be "
    "14.7 psi: BASS-II, Saffire, SAME/SAME-R, SPICE and the ACME day logs do not "
    "tabulate pressure. Dashed curves join atmospheres with equal O₂ partial pressure."
)
n_flag = int(plot["flagged"].sum())
if n_flag:
    st.caption(f"{n_flag} plotted runs have ppO₂ outside 0.5–16 psi (high-pressure, high-O₂ "
               "CFI-G and Flame Design tests). They are real test conditions, kept and flagged.")

iss = HABS["iss"]
if habitat_key != "iss":
    st.info(
        f"**{h['label']}** has an O₂ partial pressure of {h['ppo2_psi']:.2f} psi versus "
        f"{iss['ppo2_psi']:.2f} psi on the ISS, but an O₂ fraction of {h['o2_pct']:g}% versus "
        f"{iss['o2_pct']:g}%. Less inert gas absorbs heat, so materials can ignite and spread "
        f"more easily. {len(near)} standardized runs sit near this atmosphere.",
        icon=":material/lightbulb:",
    )

with st.expander("Table view of plotted runs", icon=":material/table_view:"):
    cols = ["name", "psi_id", "run_id", "fuel", "o2_pct", "pressure_psi", "ppo2_psi",
            "diluent", "outcome", "doi"]
    st.dataframe(plot.sort_values(["psi_id", "run_id"])[cols], hide_index=True,
                 width="stretch")

# ---- P6: CSV download ----
st.subheader("Download the standardized test table", anchor=False)
src = loaders.FAKE_TESTS if tests_demo else loaders.REAL_TESTS
st.download_button(
    "Download tests.csv", data=src.read_bytes(), file_name="cool_flames_tests.csv",
    mime="text/csv", icon=":material/download:", type="primary",
    help="One row per test run, all investigations, in the schema of SCHEMA.md. "
         "Blank means not reported.",
)
st.caption("Columns: psi_id, run_id, fuel, fuel_phase, fuel_class, o2_pct, pressure_psi, "
           "ppo2_psi, diluent, airflow_cms, sample_size_mm, outcome, metric_name, "
           "metric_value, metric_unit, mapping_confidence. Cite each investigation by its DOI.")

footer()

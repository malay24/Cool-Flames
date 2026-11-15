# CLAUDE.md: Freefall Fire Atlas, NASA Space Apps 2026

This file briefs Claude Code on the project. Read it fully before writing code. When something here conflicts with the code in the repo, ask the human before changing either.

> **Living-state note (updated Sun 15 Nov 2026, ~04:30 Europe/Berlin):** this file now describes the project **as built**: what changed from the original plan, what is done and what remains (section 16). The detailed, dated history of every decision (and why) is the **Change log in `TASKS.md`**; keep both current. When you finish a task, update `TASKS.md` (status, change log) and, if the change affects layout, contract, stack or status, this file too.

---

## 1. What we are building

**Challenge:** "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data" (NASA Space Apps Challenge 2026, Intermediate / Advanced).

**Brief in one line:** a web dashboard, powered by AI, that summarizes, ranks and interprets NASA's microgravity combustion investigations to deliver fire-safety insights for crewed exploration (spacecraft, space stations, Moon and Mars bases, pressurized rovers).

**Our product: the Fire Scenario Explorer** (app name "Freefall Fire Atlas", formerly "Cool Flames"). The user picks a **habitat** (ISS, Moon Base, exploration habitat, spacesuit, or an atmosphere they design by dragging a point) and a **fire scenario** (e.g. electrical overheat). The dashboard:

1. ranks the NASA investigations that matter for each phase of that fire (smoke, ignition, spread, suppression),
2. shows how close their tested conditions come to that habitat's atmosphere,
3. flags where **no data exists** (the "gap map", "0 test runs nearby", partial gravity),
4. explains why each investigation ranks where it does,
5. lets people build intuition with an illustrative animated **Flame Lab** tied back to the real experiments.

**Audience:** professors, graduate and undergraduate students, aerospace researchers and engineers.

**Positioning:** a research and reference tool, **not** an operational safety system. Never output wording such as "safe", "will not burn" or "approved". Use "not tested under these conditions", "tests show", "no data". Anything illustrative (the Flame Lab) is labelled "illustrative model, not a simulation".

**Team:** two people.

| Person | Owns |
|---|---|
| Malay | Data pipeline (`pipeline/`, `data/clean/`), ranking and scenario logic (`core/`), `data/manual/earth_vs_space.csv`, README |
| Ramneek | AI layer (`ai/`, `data/ai/`), Streamlit app (`app/`), deploy |

Only the owner edits their folders; agree changes to the data contract (section 6) and update `SCHEMA.md`. **Exception agreed on Sun 15 Nov:** Ramneek's Claude Code sessions took over Malay's open tasks R1–R5, D6–D8, P7 and P9 so the core pages could ship; all of it is logged in `TASKS.md`. Pull before editing `core/` or `pipeline/`.

**Timeline:** hackathon runs Sat 14 Nov to Sun 15 Nov 2026. Target submission Sunday 19:00 Europe/Berlin (official deadline reportedly 23:59 local; confirm in K3). Speed and robustness beat elegance. Prefer simple, readable code.

---

## 2. Domain background (read this, it drives the logic)

### Fire basics
- Fire needs fuel, oxygen, heat and a chain reaction (the fire tetrahedron). Extinguishers remove one: fuel (shut off, remove), oxygen (smother or dilute with CO2 or helium), heat (water, water mist), chain reaction (halon-type agents).
- **Diffusion flames** (fuel and oxygen meet at the flame: candle, burning fabric) are what most cabin fires are. **Premixed** flames (gas stove, explosion) are rarer here.
- **Pyrolysis:** solids do not burn directly. Heat breaks them into flammable gases. Overheated material gives off smoke before it flames, which is how fires are caught early.
- Stages: ignition, growth (flame spread), fully developed, decay or extinction.
- Measured quantities: flame spread rate, burning rate, extinction limits, **limiting oxygen concentration** (minimum O2 that sustains burning), soot and smoke output, heat radiation.

### What microgravity changes
- No buoyancy: hot gas does not rise, so a flame cannot pull in fresh air itself. Oxygen arrives only by diffusion or by cabin airflow.
- Flames are spherical, dimmer, slower, and can survive weakly right at their extinction limit.
- **Ventilation replaces gravity.** Flames burn best in a gentle breeze: too little flow starves them, too much blows them out. First crew response to a fire: shut off fans and cut power. A fraction of a cm/s of flow can keep a weak flame alive (Olson 2004).
- **Earth tests can mislead.** Some materials keep burning in microgravity where Earth screening says they would go out. BASS-II PMMA rods: flame spread sustained at 17% O2 in microgravity vs not at 18% in normal gravity (Link et al. 2018, verified). Olson 2004: thin cellulose LOI 16.5% on Earth, flames sustained at 14% O2 at 5–20 cm/s (verified). It cuts both ways: in Saffire-II one silicone sample burned completely in 1 g but not in low gravity.
- **Smoke does not rise.** Detectors sit in the ventilation flow. Smoke particles differ from Earth smoke (SAME, SAME-R). The ISS detector often missed small particles from Teflon and Kapton, common in electronics (Meyer et al. 2018).
- **Cool flames:** FLEX found large n-alkane droplets that kept burning in a low-temperature, camera-invisible regime after the visible flame went out (Nayagam et al. 2014: n-decane at 14–21% O2, 0.5 atm; not at 25%). A hidden hazard for liquid fuels.
- **More soot** in microgravity gas flames, because slow flow gives soot more time to form (SPICE).
- **Scale matters:** Saffire burned large samples (94 x 40.6 cm) on Cygnus; flame behaviour depends on scale, so small-sample tests are not enough.
- **Partial gravity is untested.** Moon (1/6 g) and Mars (about 3/8 g) give weak buoyancy (buoyant flows above 20 cm/s per Olson 2004), which may act like the ideal gentle breeze, so materials may be **most** flammable there. PSI has no partial-gravity data. E-FIELD imitates buoyancy with an ion wind. Microgravity and 1 g results bound the in-between. Future data: FM2, LUCI.

### Atmospheres (habitat presets, `core/scenarios.py` HABITATS)

| Preset key | Label | O2 % | Total pressure (psi) | ppO2 (psi) | gravity_g | Source |
|---|---|---|---|---|---|---|
| `iss` | ISS | 21 | 14.7 | 3.09 | 0 | brief |
| `moon_brief` | Moon Base / pressurized rover | 30 | 10.2 | 3.06 | 0.166 | brief ("30%+ O2 at 10.2 psi or less") |
| `exploration` | Exploration habitat (NASA) | 34 | 8.2 | 2.79 | 0.166 | NASA exploration atmosphere, revised in 2012 |
| `suit` | Spacesuit | 100 | 4.3 | 4.30 | 0 | brief (ISS spacewalk suit) |
| `custom` | Custom atmosphere | user | user | computed | 0 / 0.166 / 0.38 | designed on the Scenario page (session only) |

`partial_gravity` is True for the Moon base and exploration habitat (and a designed Moon/Mars atmosphere). `gravity_g` drives only the illustrative animations.

Key insight to surface in the UI: the exploration habitat has **lower** O2 partial pressure than the ISS but a **higher** O2 fraction. Less inert gas (diluent) absorbs heat, so materials ignite and spread more easily. The gap map and designer draw iso-ppO2 curves to show this.

### Fire types and coverage
- **Electrical overheating is the most likely ignition source** in a spacecraft, so solids and smouldering insulation matter most.
- Metal fires (aluminium, titanium in pure O2) and rocket or propellant fires are **out of scope** (no PSI data / excluded by the brief).

---

## 3. Data source: NASA Physical Sciences Informatics (PSI)

- 24 combustion investigations, 22 experiment tables. Public, no login, CC0 licensed. **Real counts (recomputed):** about **2,000 test runs** in the tables (1,982; several tables pad with blank rows, so the brief's "~2,900" was too high), **1,858 standardized** into `tests.csv` from 19 tables, **1,009** with both O2 and pressure.
- Endpoint used by `pipeline/fetch_psi.py`: `https://psi.nasa.gov/geode-py/ws/repo/investigations/<PSI-ID>`. Tables come from `https://psi.nasa.gov/geode-py/ws/studies/{accession}/download?source=datamanager&file={file_name}` (the record's `remote_url` 404s). **Not formally documented.** Read field names from `data/raw/`.
- Each investigation record contains: objective, approach, hypothesis, research impacts, hardware, flight platform, dates, publications, DOI, and an experiment table. Column inventory: `data/raw/columns.md` (`python pipeline/inventory.py`).
- **PSI requires citing each investigation by its DOI.** Every place we show an investigation shows or links its DOI (all 24 listed in README).
- Raw data is committed (`data/raw/`) so we never depend on the endpoint during judging.

### Investigations by fire-safety area

| Area | Investigations (PSI ID) | Runs (raw / standardized) |
|---|---|---|
| Prevention | BASS (PSI-26), BASS-II (PSI-25), Saffire-I (PSI-98), Saffire-II (PSI-99), Saffire-III (PSI-100), ACME BRE (PSI-20) | 122/0, 129/129, 2/2, 9/9, 2/2, 18/18 |
| Suppression | FLEX (PSI-69), FLEX-2 (PSI-68), CFI (PSI-39) | 274/274, 8/8 (summary rows), 87/87 |
| Detection | SAME (PSI-102), SAME-R (PSI-101), DAFT / DAFT-2 (PSI-47) | 8/8, 109/109, 2/0 |
| Basic flame science | SPICE (PSI-107), SLICE (PSI-106), ACME CLD (PSI-21), Flame Design (PSI-10), s-Flame (PSI-23), E-FIELD (PSI-22), CFI-G (PSI-159) | 469, 12, 32, 327, 18, 21, 333 (all standardized) |
| Modelling (ground studies, text only) | PSI-62, PSI-115, PSI-117, PSI-142, PSI-60 | text only (PSI-142's table indexes paper figures: 0 runs) |

Not standardized on purpose: BASS (run log, no conditions), DAFT (dust sampling, no combustion), PSI-142 (figure index).

### Hardware context
- Combustion Integrated Rack (CIR): six ACME gas-flame experiments, plus FLEX, FLEX-2, CFI (droplets in the Multi-user Droplet Combustion Apparatus).
- Microgravity Science Glovebox (MSG): BASS, BASS-II, SPICE, SLICE (same fan-driven flow duct).
- Cygnus cargo vehicle after leaving the ISS: Saffire I to III, large-scale fires with no crew at risk.

### Fuel type to investigation map

| Fuel type | Examples | Spacecraft relevance | PSI coverage |
|---|---|---|---|
| Solid, flaming | Fabric, paper, plastics (PMMA, Nomex, SIBAL cotton-fiberglass) | Cabin materials, clothing, bags | BASS, BASS-II, Saffire I to III |
| Solid, smouldering / overheating | Wire insulation, foam | Most likely way a fire starts | SAME, SAME-R |
| Liquid | Fuel droplets, sprays, pools | Lubricants, cleaning fluids, fuel leaks | FLEX, FLEX-2, CFI |
| Gas | Leaking gas jets | Oxygen or fuel line leaks | ACME (5 experiments), CFI-G, SPICE, SLICE |
| Electrical | Overheated wiring and avionics | #1 ignition source | Indirectly via SAME smoke tests |
| Metal | Aluminium, titanium in pure O2 | Oxygen systems | Not covered |

---

## 4. Tech stack (as built)

| Layer | Choice |
|---|---|
| Language | **Python 3.12** (venv; 3.11 was not installed). Streamlit Cloud: pick 3.12 |
| Data fetch / handling | `requests`, `pandas` |
| Summaries, tags, key findings | Written **offline by Claude (Anthropic)** from each PSI record's own text, stored in `data/ai/ai_fields.json`, merged by `ai/tag_summarize.py --import`. No Gemini/Azure offer existed (K4 cut), so no key is needed for this |
| Column mappings | Hand-written (`mapping_confidence: hand`), checked by `pipeline/spot_check.py`; `ai/map_columns.py` is an unused stub (A5 cut) |
| Q&A retrieval | `sentence-transformers` (`all-MiniLM-L6-v2`) + FAISS, **hybrid with keyword scoring** (70/30); falls back to NumPy, then keyword-only |
| Q&A answers | Optional Google Gemini via a free **AI Studio** key (`GEMINI_API_KEY`, `GEMINI_MODEL`); without a key the Ask page shows the source passages with DOIs |
| Ranking | plain Python, transparent weighted score |
| Charts | Plotly (palette from the dataviz reference palette, validated light + dark) |
| Animations | Streamlit **Custom Components v2** (`st.components.v2.component`) with **p5.js 1.11.1** and **three.js 0.170.0** from cdn.jsdelivr.net; static fallback offline; honours `prefers-reduced-motion` |
| App | Streamlit 1.67 with `st.navigation` router, theme in `.streamlit/config.toml` |
| Hosting | Streamlit Community Cloud (fallback: Hugging Face Spaces) |

**Hard rule (kept):** all AI outputs are generated once, saved to files and committed. The deployed app runs with **no API key**; only the Ask page can use one.

`requirements.txt` is pinned (streamlit 1.67.0, pandas 3.1.1, numpy 2.5.4, plotly 7.1.0, requests 2.34.2, python-dotenv 1.2.4, google-genai 3.3.0, sentence-transformers 6.3.0, faiss-cpu 1.16.0, torch 2.15.0 **CPU wheel on Linux** via the PyTorch CPU index and a platform marker). Dev tools: `requirements-dev.txt` (adds pytest 9.2.0).

---

## 5. Repo layout (as built)

```
cool-flames/
  CLAUDE.md               this file (current state + status, section 16)
  TASKS.md                task board + dated Change log (read first)
  SCHEMA.md               the data contract (section 6), source of truth
  README.md               what it is, how to run, data rules, all 24 DOIs, AI-use note
  requirements.txt        pinned deploy deps;  requirements-dev.txt adds pytest
  .env.example            GEMINI_API_KEY=, GEMINI_MODEL=   (Ask page only)
  .streamlit/config.toml  theme (dark-first + light), fonts, toolbarMode=minimal
  docs/
    DEMO_SCRIPT.md        under-2-minute demo, real numbers
    SUBMISSION.md         submission form text (links still placeholders)
  app/                    Streamlit (Ramneek)
    Home.py               ENTRY POINT + router: page config, logo, CSS, sidebar habitat picker, st.navigation
    views/                one file per page (moved from app/pages/)
      home.py             hero (three.js), stats, "Start here", habitat insight
      scenario.py         habitat designer (p5.js, two-way) + ranking tabs, weights, warnings
      gap_map.py          Plotly gap map + CSV download
      flame_lab.py        illustrative animated flame (p5.js) + "what NASA tested here"
      overview.py         "Investigations": cards, filters, Earth-vs-space cards
      dossier.py          "Study dossier": one investigation in depth (?id=PSI-99), similar studies
      compare.py          2-4 investigations side by side
      ask.py              cited Q&A
      earth_benefits.py   quotes from the records' research-impacts text
    components/
      __init__.py         theme tokens, CSS, page_header, stat_row, cards, warning_card, sidebar
      data.py             st.cache_data wrappers around core.loaders; habitats() incl. custom
      interactive.py      registers the 3 v2 components (hero, flame_lab, habitat_designer)
    static/               logo.svg, icon.svg, js/ (hero.js, flame_lab.js, habitat_designer.js, interactive.css)
  core/                   pure logic, no Streamlit imports
    scenarios.py          HABITATS (+gravity_g), resolve_habitat(), SCENARIOS (+short, icon), PHASE_AREA/ICONS/LABELS, HISTORY
    ranking.py            rank(); accepts a habitat key or dict
    warnings.py           get_warnings(); accepts a habitat key or dict
    loaders.py            ROOT, load_tests(), load_investigations(), load_earth_vs_space(); fake-data fallback
  pipeline/               offline data build
    fetch_psi.py          records + tables to data/raw/
    inventory.py          writes data/raw/columns.md
    units.py              unit conversions
    build_tests.py        mappings -> data/clean/tests.csv   (run: python -m pipeline.build_tests)
    spot_check.py         20 cleaned rows vs raw cells       (python -m pipeline.spot_check)
    build_ranges.py       -> data/clean/ranges.csv           (python -m pipeline.build_ranges)
    mappings/             19 table mappings + _FORMAT.md
  ai/                     offline AI build + Q&A
    tag_summarize.py      facts from data/raw/ + AI fields -> data/ai/investigations.json
    llm.py                Gemini helper (lazy, Ask page only)
    prompts/tag_summarize.md
    build_index.py        chunks + embeddings + FAISS -> data/ai/index/
    qa.py                 hybrid retrieval, cited answers, fallbacks
    map_columns.py        stub (A5 cut)
    dossier.py            dossier facts from data/raw/ (record text, table columns, instruments) + similar studies
  data/
    raw/                  24 records, 22 tables, columns.md
    clean/                tests.csv (1,858 rows), ranges.csv
    ai/                   investigations.json, ai_fields.json, batch_input.jsonl, index/
    manual/               earth_vs_space.csv (8 sourced rows)
    fake/                 stub data for app development
  tests/                  pytest (129): units, schema, build_tests parsing, ranking, warnings, Q&A, dossier, every app page
```

`core/` must not import Streamlit. `app/` imports from `core/` and reads files from `data/`. The app never calls the PSI endpoint.

---

## 6. Data contract (mirror of SCHEMA.md)

### 6.1 `data/clean/tests.csv`, one row per test run

| Column | Type | Notes |
|---|---|---|
| `psi_id` | str | e.g. `PSI-99` |
| `run_id` | str | original run label, or the row's position in the raw table |
| `fuel` | str | as written in the table |
| `fuel_phase` | enum | `solid`, `liquid`, `gas` |
| `fuel_class` | enum | `cabin_material`, `idealized` |
| `o2_pct` | float | % by volume (mole fraction x 100) |
| `pressure_psi` | float | converted from atm, kPa, mmHg, bar |
| `ppo2_psi` | float | `o2_pct / 100 * pressure_psi` |
| `diluent` | str | `N2`, `He`, `CO2`, `mixed`; blank if unknown |
| `airflow_cms` | float | cm/s; blank if not reported |
| `sample_size_mm` | float | largest dimension; blank if not reported |
| `outcome` | enum | `burned`, `extinguished`, `no_ignition`, `unknown` |
| `metric_name` / `metric_value` / `metric_unit` | str / float / str | main measurement |
| `mapping_confidence` | enum | `hand`, `llm_checked`, `llm_unchecked` |

Rules (as applied):
- **Blank means "not reported". Never fill blanks with 0.** Zero airflow is real.
- **Strict pressure policy:** pressure is never assumed (no default 14.7 psi). Tables without a pressure column stay blank and are left off the gap map.
- **List-valued conditions are blanked and flagged** (e.g. `21; 26.5; 40`, `~30% and ~21%`); per-day/per-fuel summary tables (ACME BRE, CLD, E-FIELD, SLICE, FLEX-2) map only fuel/run_id/constants.
- `parse_number` ignores note references (`Note 4`) and chemical formulas (`LOW O2`), takes midpoints for `x to y`.
- Unphysical values (pressure ≤ 0, negative airflow) are blanked and flagged. ppO2 outside 0.5–16 psi is flagged, not dropped (72 real high-O2/high-pressure CFI-G and Flame Design runs).
- One main metric per row; enums lowercase; validated by `tests/test_schema.py`.

Mapping file format: `pipeline/mappings/_FORMAT.md` (columns with unit hints, constants, metric, `outcome_from`, `diluent_from`, **`require`** to skip non-run rows such as footnotes and flow-visualisation runs).

### 6.2 `data/ai/investigations.json`, one object per investigation

Contract fields: `psi_id`, `name`, `doi`, `area`, `fuel_types`, `hardware`, `platform`, `summary_3line`, `key_findings`, `n_runs`, `n_publications`, `o2_range`, `pressure_range`, `airflow_range`, `test_scale`.

- **`fuel_types` = fuel PHASES** (`solid`/`liquid`/`gas`), from a hand map of section 3; used by ranking.
- **Additive fields:** `fuels` (material names, display), `title`, `n_standardized_runs`, `sample_size_range`, `start_date`, `end_date`, `publications`, `ai_source`.
- `n_runs` = standardized count when the table is mapped, else non-empty raw rows; PSI-142 = 0.
- Ranges come from `data/clean/ranges.csv` (D8), never from AI. `area` and `test_scale` come from hand maps (CLAUDE.md section 3). DOIs are copied from the raw record.
- Rebuild: `python ai/tag_summarize.py --import data/ai/ai_fields.json`.

### 6.3 `data/manual/earth_vs_space.csv`, hand-curated

Columns: `material`, `measure`, **`flag`** (added: short verdict shown in the app), `value_1g`, `value_ug`, `unit`, `finding`, `source`, `source_url`. 8 rows, every number checked against the source text (Link et al. 2018; Olson 2004; Nayagam et al. 2014; the PSI-99 table). Findings in both directions are kept. No FLEX CO2-limit row: the Dietrich 2014 numbers could not be verified, so they were left out. Do not add rows from memory.

### 6.4 Unit conversions (`pipeline/units.py`)

1 atm = 14.696 psi; 1 kPa = 0.14504 psi; 1 mmHg = 0.019337 psi; 1 bar = 14.504 psi; mole fraction 0.21 = 21%.

### 6.5 Fake data (`data/fake/`)

10 rows of `tests.csv`, 3 investigations (fake DOIs `10.0000/demo-*`). Loaders fall back to them and pages show a "demo data" badge.

---

## 7. Pipeline (status: complete)

1. `python pipeline/fetch_psi.py` → `data/raw/` (24 records, 22 tables). Done.
2. `python pipeline/inventory.py` → `data/raw/columns.md`. Done.
3. Hand mappings for **19 tables** in `pipeline/mappings/` (core 4 by Malay; 15 more in D6). BASS, DAFT and PSI-142 deliberately skipped.
4. `python -m pipeline.build_tests` → `data/clean/tests.csv` (1,858 rows, 0 validation errors, flags printed).
5. `python -m pipeline.spot_check` → 20 rows vs raw; found and fixed 4 bugs (`Note 4` as 4 mm/s, `LOW O2` as 200%, collapsed O2 lists, Saffire-II footnote rows counted as runs).
6. `python -m pipeline.build_ranges` → `data/clean/ranges.csv`, then `python ai/tag_summarize.py --import data/ai/ai_fields.json`.

---

## 8. Scenarios and ranking (`core/`)

### 8.1 Scenarios (`core/scenarios.py`)

| Scenario key | Label | Phases (in order) | Relevant fuel phases |
|---|---|---|---|
| `electrical_overheat` | Electrical overheat (wiring, avionics) | smoke, ignition, spread, suppression | solid |
| `cabin_material_fire` | Cabin material fire (fabric, plastics) | ignition, spread, suppression | solid |
| `liquid_leak` | Liquid leak (lubricant, cleaning fluid) | ignition, spread, suppression | liquid |
| `gas_leak` | Gas leak (O2 or fuel line) | ignition, spread, suppression | gas |
| `oxygen_rich_cabin` | Oxygen-rich cabin (Apollo 1 type) | ignition, spread, suppression | solid, gas |
| `lunar_dust` | Lunar dust and detectors | smoke | none (detection only) |

Each scenario also has `short` and `icon` (UI). Phase to area: `smoke` -> `detection`; `ignition`, `spread` -> `prevention`; `suppression` -> `suppression`; area `basic` gets 0.5 credit. `resolve_habitat(key_or_dict)` turns a preset key or a designed atmosphere dict into a validated habitat.

Historical context (static): Apollo 1 (1967), Apollo 13 (1970), Mir (1997); all involved extra oxygen.

### 8.2 Ranking score (`core/ranking.py`)

```
score = w1 * area_match + w2 * condition_overlap + w3 * fuel_realism + w4 * data_richness
```

Default weights 0.35 / 0.30 / 0.20 / 0.15, adjustable in the app; **weights are divided by their sum** so scores stay in [0, 1]. Components exactly as originally specified (area match with fuel relevance, nearest-run distance with `1 - d/0.5`, fuel realism by dominant `fuel_class` (0 if no standardized rows), data richness with the large-scale bonus). Template explanations, no AI. `rank()` accepts a habitat key **or dict**. The Scenario page ranks only studies with area_match > 0 by default (toggle for all).

**Sanity check passes:** `moon_brief` + `electrical_overheat`, smoke → SAME-R 0.648, SAME 0.628, then Flame Design 0.556 (`tests/test_ranking.py`, `tests/test_app_pages.py`).

### 8.3 Warning cards (`core/warnings.py`)

Five rules as specified (detector blind spot, hidden hazard, no data yet for partial gravity, Earth tests not conservative, outside tested range / conditions not reported), each with sources from section 14. `get_warnings()` accepts a habitat key or dict. Wording is tested for banned words.

---

## 9. App (as built, `app/`)

**Shell (`app/Home.py`):** logo, theme CSS, **sidebar habitat picker + atmosphere card** (O2, psi, ppO2, gravity, partial-gravity note) on every page, grouped navigation. Footer on every page: research tool disclaimer, NASA PSI (CC0), every claim links its DOI. Theme: "mission control", dark-first navy with flame-orange accent plus a matching light theme (Space Grotesk headings, Inter body).

| Nav group | Page (file) | Content |
|---|---|---|
| — | Home (`views/home.py`) | three.js animated hero that follows the selected habitat, stat tiles, "Start here" cards, habitat ppO2 insight, Apollo/Mir history |
| Explore | Scenario Explorer (`views/scenario.py`) | **Habitat designer** (drag a point on O2-vs-pressure; on release Python re-ranks for a "Custom atmosphere"; presets clickable; Orbit/Moon/Mars; exact inputs), scenario pills, phase tabs, weight sliders (sidebar), stacked score chart, result cards, warning cards |
| Explore | Gap map (`views/gap_map.py`) | 1,009 runs, x = psi, y = O2 %, colour + shape by area, habitat stars, iso-ppO2 curves (2.8/3.1/4.3), "runs near habitat" metric, table view, CSV download |
| Explore | Flame Lab (`views/flame_lab.py`) | Illustrative p5.js flame: gravity, O2, airflow, solid/droplet, six "Try this" presets (incl. turn off the fans, FLEX cool flame); lists matching NASA studies, "no data yet" for Moon/Mars, Earth-vs-space for 1 g; rules + sources in "How this animation works" |
| Explore | Investigations (`views/overview.py`) | 24 cards (summary, fuels, condition chips, runs, DOI, key findings, **Open dossier** link), filters, Earth-vs-space flagged cards |
| Explore | Study dossier (`views/dossier.py`) | One investigation in depth, deep link `?id=PSI-99`: identity (platform, hardware, dates, PI), AI summary, objective/hypothesis/approach/impacts **quoted verbatim**, "what was tested" (sample, conditions, measurements from the raw table columns, sorted by keyword rules; what varied), instruments named in the record with the quoting sentence, closest run to the habitat, runs chart (fields with ≥5 values), similar studies (60% record-text embeddings + 40% shared area/fuel phase/hardware/O₂), publications, standardized + raw tables, CSV. Linked from Investigations cards, Scenario results and Compare |
| Tools | Compare (`views/compare.py`) | 2–4 studies side by side + similarities/differences |
| Tools | Ask (`views/ask.py`) | cited Q&A, example pills, works without a key |
| About | Earth benefits (`views/earth_benefits.py`) | 3 items quoted from the records' research-impacts text with DOIs (no water-mist / firefighter-gear claims: not in PSI) |

---

## 10. AI layer (as built, `ai/`)

1. **Summaries/tags:** `ai/tag_summarize.py` copies facts from `data/raw/` and hand maps; AI fields (`fuels`, `fuel_types`, `summary_3line`, `key_findings`) come from `data/ai/ai_fields.json`, written by Claude from record text only; validated (3 lines, 1–4 findings, banned wording). `--export-batch` writes prompts; `--llm` keeps an optional Gemini path. **A human should still read every summary once.**
2. **Column mapping:** done by hand (A5 cut).
3. **Dossiers (`ai/dossier.py`):** no generation. Record text and table columns are shown verbatim (footnote rows dropped with the mapping's `require`); instruments come from a fixed vocabulary scan with the source sentence; similar studies = 0.6 × cosine of mean chunk embeddings from `data/ai/index/` + 0.4 × shared attributes (area 0.4, fuel phase 0.3, hardware 0.2, O₂ overlap 0.1).
4. **Q&A:** `ai/build_index.py` (44 chunks, ~500 tokens, overlap 50) → `data/ai/index/`; `ai/qa.py` hybrid retrieval, declines off-topic questions, Gemini answer with DOIs if a key exists, else passages with DOIs.

---

## 11. Conventions

- Python 3.12, type hints on public functions, docstrings one line where obvious.
- `pathlib` for paths; `ROOT` in `core/loaders.py`.
- Pure functions in `core/`; side effects only in `pipeline/`, `ai/` and `app/`.
- Cache data loading in the app with `st.cache_data`.
- Small commits to `main`, messages `area: what changed`, plus the Co-Authored-By line when Claude writes them.
- `pytest` must pass (129 tests) before every commit.
- **Restart `streamlit run app/Home.py` after changing `core/`, `pipeline/`, `.streamlit/config.toml` or `app/static/js/`.** Streamlit only hot-reloads files under `app/`; a stale server raises errors like `TypeError: unhashable type: 'dict'` in `rank()`.
- Never commit `.env`, `.streamlit/secrets.toml` or API keys.
- Do not add packages without need; keep the deploy small.
- Do not fabricate data, DOIs, numbers or citations. Verify sources before adding them (R4 checked every number against the paper text).
- Animations: honest labels ("illustrative"), cite each rule, reduced-motion support, static fallback.

---

## 12. Task list (status as of Sun 15 Nov, ~04:30)

| ID | Task | Owner | Status |
|---|---|---|---|
| K1 | Create repo with layout | Malay | Done |
| K2 | Agree schema, SCHEMA.md | Both | Done |
| K3 | Confirm deadline and team registration | Ramneek | **To do** |
| K4 | LLM API key | Ramneek | Cut (no LLM offer; AI Studio key optional for Ask) |
| K5 | Fake data | Malay | Done |
| D1–D5 | Fetch, inventory, units, core mappings, build_tests | Malay | Done |
| D6 | Map the other tables | Malay → Ramneek session | Done (15 tables, hand) |
| D7 | Spot-check 20 rows | Ramneek session | Done (4 bugs fixed) |
| D8 | Ranges and run counts | Ramneek session | Done |
| R1, R2, R3, R5 | Scenarios, ranking, sanity check, warnings | Ramneek session | Done |
| R4 | earth_vs_space.csv | Ramneek session | Done (8 verified rows) |
| A1, A2 | Tags and summaries for all 24 | Ramneek | Done (written by Claude from record text) |
| A3, A4 | Q&A index and function | Ramneek | Done |
| A5 | Column-mapping prompt | Ramneek | Cut (mappings by hand) |
| P1–P6, P8 | App skeleton, Overview, Scenario, Gap map, warnings, CSV, Ask | Ramneek | Done |
| P7, P9 | Compare, Earth benefits | Ramneek session | Done |
| — | Theme, navigation, Flame Lab, habitat designer, animated hero (extra) | Ramneek | Done |
| S1 | First deploy to Streamlit Cloud | Ramneek | **To do** (ready) |
| S2 | Test public link (private window, phone) | Malay | **To do** (after S1) |
| S3 | README | Ramneek session | Done |
| S4 | Demo script | Both | **In progress** (draft in `docs/DEMO_SCRIPT.md`; time it on the live app) |
| S5 | Record demo video | Both | **To do** |
| S6 | Submission form text | Ramneek | **In progress** (draft in `docs/SUBMISSION.md`; add links) |
| S7 | Final check and submit | Both | **To do** |

**30 of 39 done, 2 cut, 7 open.**

---

## 13. Demo story (see `docs/DEMO_SCRIPT.md`)

1. Hook: Apollo 1, Apollo 13 and Mir all involved extra oxygen; the Moon Base plans 30%+ O2. (Optional 10 s Flame Lab opener: same fire on Earth vs on the ISS.)
2. Investigations: 24 studies, **about 2,000 test runs, 1,858 standardized**, summarized, every card with a DOI.
3. Scenario: Moon base + electrical overheat. Smoke phase ranks **SAME-R and SAME** first with the detector blind-spot warning. Move a weight slider to show why.
4. Gap map (or the designer): the Moon base sits where few tests exist: **64 runs nearby vs 341 near ISS air, 0 near the spacesuit**; dragging to 9 psi / 40% O2 shows "0 test runs nearby". ppO2 curves explain the higher fire risk.
5. No data yet: partial gravity is untested; FM2 and LUCI will fill it.
6. Close: CSV export for modellers, every claim tied to a DOI, research tool disclaimer.

Our edge: phase-by-phase ranking with explanations, the detector blind-spot story, the ppO2 framing, the designed-atmosphere data-gap check, and the honest illustrative Flame Lab.

---

## 14. Key references

- Urban et al. 2019, Flame spread: effects of microgravity and scale, Combustion and Flame 199 (Saffire-I/II)
- Jomaas et al. 2015, Fire safety in space: beyond flammability testing of small samples, Acta Astronautica 109
- Combustion of solids in microgravity: BASS-II results (NTRS 2016)
- **Link et al. 2018, The Effect of Gravity on Flame Spread over PMMA Cylinders, Scientific Reports, https://doi.org/10.1038/s41598-017-18398-4** (verified: 17% vs 18%; faster μg spread below 19% O2)
- **Olson 2004, Most Probable Fire Scenarios in Spacecraft and Extraterrestrial Habitats: Why NASA's Current Test 1 Might Not Always Be Conservative, NASA/TM-2004-213114, https://ntrs.nasa.gov/citations/20040084156** (verified: 16.5% vs 14%; fraction-of-a-cm/s flames; upwind spread; >20 cm/s lunar buoyant flow)
- Ferkul, Kralik, Liao 2026, Material flammability at lunar and Martian gravity (LPSC) (FM2)
- Nayagam et al. 2012, Can cool flames support quasi-steady alkane droplet burning?, Combustion and Flame 159 (FLEX)
- **Nayagam, Dietrich, Hicks, Williams 2014, Cool-flame extinction during n-alkane droplet combustion in microgravity, https://ntrs.nasa.gov/citations/20140006750** (verified)
- Dietrich et al. 2014, Droplet combustion experiments aboard the ISS, Microgravity Sci. Technol. (FLEX) (numbers not verified; not used for data)
- Urban et al. 2009, Smoke particle sizes in low-gravity, SAE (SAME)
- Meyer et al. 2018, Spacecraft smoke detector performance in low gravity, Fire Safety Journal (SAME, SAME-R)
- Impacts of reduced-pressure atmospheres on ECLSS (NTRS 2026)

Links: PSI repository `https://psi.nasa.gov/physci/repo`; NTRS API `https://ntrs.nasa.gov/api/citations/search`.

---

## 15. How Claude Code should work on this repo

- Start by reading this file, `SCHEMA.md` and the **Change log in `TASKS.md`**; `git pull` first.
- Confirm the task ID with the human; stay inside that owner's folders unless the human says otherwise (and log it).
- After changing data code: `python -m pipeline.build_tests`, `python -m pipeline.build_ranges`, `python ai/tag_summarize.py --import data/ai/ai_fields.json`, then `pytest`.
- After changing the app: restart Streamlit, check every page (AppTest page tests cover load errors; check animations in a real browser).
- If a PSI table is ambiguous, stop and ask rather than guess.
- Keep the app working at every commit: the team may deploy at any moment.
- When a task finishes: update `TASKS.md` (status, Progress, Ready now, Change log) and section 16 below.

---

## 16. Current status and what remains (Sun 15 Nov 2026, ~04:30)

**Built and tested (129 tests pass; all pages load on real and fake data; animations checked in headless Chrome in dark/light, desktop/phone, reduced motion):**
- Full data pipeline: 19 tables standardized, spot-checked, ranges built.
- All 24 investigations summarized and tagged; Earth-vs-space table with verified sources.
- Ranking, warnings, custom-atmosphere support in `core/`.
- App: Home (animated hero), Scenario Explorer (+ habitat designer), Gap map, Flame Lab, Investigations, **Study dossier** (added Sun ~14:00, closes the brief's per-investigation detail: objectives, sample, conditions, what varied, sensors/measurements, similar studies), Compare, Ask, Earth benefits; theme and grouped navigation.
- README, demo script draft, submission text draft.

**Not yet done (in order):**
1. **Push** the local commits (`git pull --rebase` then `git push origin main`; at ~04:30 there were 18 unpushed commits and nothing new on the remote).
2. **K3** Confirm the official deadline and team registration on spaceappschallenge.org.
3. **A human reads all 24 summaries once** (`data/ai/ai_fields.json` or the Investigations page) and fixes anything wrong; the AI-use note says the team checked them.
4. **S1** Deploy: share.streamlit.io → repo `malay24/Cool-Flames`, branch `main`, main file `app/Home.py`, Python 3.12; secrets optional (`GEMINI_API_KEY`, `GEMINI_MODEL`). If install fails (e.g. the torch CPU index line), remove the three Ask-only lines from `requirements.txt` (Ask then uses keyword search) or use Hugging Face Spaces.
5. **S2** Test the public link in a private window and on a phone (check animations load from the CDN).
6. **S4** Time the demo script on the live app; adjust numbers if the data changes.
7. **S5** Record the video (under 2 minutes).
8. **S6** Fill the form from `docs/SUBMISSION.md`; add the app, video and repo links.
9. **S7** Make the repo public, final check, submit.

**Optional if time allows:** coverage-timeline animation on the Gap map (proposed, not built); a Gemini key in Streamlit secrets for written Ask answers.

**Known caveats:** fonts and animation libraries load from Google Fonts / jsDelivr (static fallbacks offline); `n_runs` totals differ from the brief because padded blank rows are no longer counted; ACME/FLEX-2 summary tables carry fuels but no conditions by design.

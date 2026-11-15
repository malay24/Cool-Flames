# CLAUDE.md: Cool Flames, NASA Space Apps 2026

This file briefs Claude Code on the project. Read it fully before writing code. When something here conflicts with the code in the repo, ask the human before changing either.

> **Living-state note (added 2026-11-15):** this file is the original source-of-intent briefing and is kept verbatim. Where our build has since deviated from it (e.g. the pressure policy, dropping BASS from the core tables), the authoritative current state and the reasons are recorded in `TASKS.md` under **Change log**. Read `TASKS.md` (Working agreement + Change log) before starting a session.

---

## 1. What we are building

**Challenge:** "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data" (NASA Space Apps Challenge 2026, Intermediate / Advanced).

**Brief in one line:** a web dashboard, powered by AI, that summarizes, ranks and interprets NASA's microgravity combustion investigations to deliver fire-safety insights for crewed exploration (spacecraft, space stations, Moon and Mars bases, pressurized rovers).

**Our product: the Fire Scenario Explorer.** The user picks a **habitat** (ISS, Moon Base, exploration habitat, spacesuit) and a **fire scenario** (e.g. electrical overheat). The dashboard:

1. ranks the NASA investigations that matter for each phase of that fire (smoke, ignition, spread, suppression),
2. shows how close their tested conditions come to that habitat's atmosphere,
3. flags where **no data exists** (the "gap map"),
4. explains why each investigation ranks where it does.

**Audience:** professors, graduate and undergraduate students, aerospace researchers and engineers.

**Positioning:** a research and reference tool, **not** an operational safety system. Never output wording such as "safe", "will not burn" or "approved". Use "not tested under these conditions", "tests show", "no data".

**Team:** two people.

| Person | Owns |
|---|---|
| Malay | Data pipeline (`pipeline/`, `data/clean/`), ranking and scenario logic (`core/`), `data/manual/earth_vs_space.csv`, README |
| Ramneek | AI layer (`ai/`, `data/ai/`), Streamlit app (`app/`), deploy |

Only the owner edits their folders. Changing the data contract (section 6) requires agreement from both, then an update to `SCHEMA.md`.

**Timeline:** hackathon runs Sat 14 Nov to Sun 15 Nov 2026. Target submission Sunday 19:00 Europe/Berlin. Speed and robustness beat elegance. Prefer simple, readable code.

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
- **Ventilation replaces gravity.** Flames burn best in a gentle breeze: too little flow starves them, too much blows them out. First crew response to a fire: shut off fans and cut power.
- **Earth tests can mislead.** Some materials keep burning in microgravity where Earth screening says they would go out. BASS: PMMA burned at 17% O2 in microgravity vs 18% in Earth gravity. Olson 2004: opposed-flow flames sustained at 14% O2.
- **Smoke does not rise.** Detectors sit in the ventilation flow. Smoke particles differ from Earth smoke (SAME, SAME-R). The ISS detector often missed small particles from Teflon and Kapton, common in electronics (Meyer et al. 2018).
- **Cool flames:** FLEX found heptane droplets that kept burning invisibly at roughly 500 to 800 K after the visible flame went out. A hidden hazard for liquid fuels.
- **More soot** in microgravity gas flames, because slow flow gives soot more time to form (SPICE).
- **Scale matters:** Saffire burned large samples (94 x 40.6 cm) on Cygnus; flame behaviour depends on scale, so small-sample tests are not enough.
- **Partial gravity is untested.** Moon (1/6 g) and Mars (about 3/8 g) give weak buoyancy, which may act like the ideal gentle breeze, so materials may be **most** flammable there. PSI has no partial-gravity data. E-FIELD imitates partial gravity. Microgravity and 1 g results bound the in-between. Future data: FM2, LUCI.

### Atmospheres (habitat presets)

| Preset key | Label | O2 % | Total pressure (psi) | ppO2 (psi) | Source |
|---|---|---|---|---|---|
| `iss` | ISS | 21 | 14.7 | 3.09 | brief |
| `moon_brief` | Moon Base / pressurized rover (brief) | 30 | 10.2 | 3.06 | brief ("30%+ O2 at 10.2 psi or less") |
| `exploration` | Exploration habitat (NASA plan) | 34 | 8.2 | 2.79 | NASA exploration atmosphere, revised in 2012 |
| `suit` | Spacesuit | 100 | 4.3 | 4.30 | brief |

Key insight to surface in the UI: the exploration habitat has **lower** O2 partial pressure than the ISS but a **higher** O2 fraction. Less inert gas (diluent) absorbs heat, so materials ignite and spread more easily. Plot iso-ppO2 lines on the gap map to show this.

### Fire types and coverage
- **Electrical overheating is the most likely ignition source** in a spacecraft, so solids and smouldering insulation matter most.
- Metal fires (aluminium, titanium in pure O2) and rocket or propellant fires are **out of scope** (no PSI data / excluded by the brief).

---

## 3. Data source: NASA Physical Sciences Informatics (PSI)

- 24 combustion investigations, about 2,900 test runs across 22 experiment tables. Public, no login, CC0 licensed.
- Endpoint used by `pipeline/fetch_psi.py`: `https://psi.nasa.gov/geode-py/ws/repo/investigations/<PSI-ID>` (e.g. `PSI-99`). **Not formally documented.** Run the fetch first and inspect the real JSON before writing parsers. Do not assume field names; read them from `data/raw/`.
- Each investigation record contains: objective, approach, hypothesis, research impacts, hardware, flight platform, dates, publications, DOI, and an experiment table (one row per test). Table columns differ per investigation (oxygen fraction, pressure, airflow, fuel, sample size, ignition and burn times, spread rates, extinction).
- **PSI requires citing each investigation by its DOI.** Every place we show an investigation must show or link its DOI.
- Raw data is committed to the repo (`data/raw/`) so we never depend on the endpoint during judging.

### Investigations by fire-safety area

| Area | Investigations (PSI ID) | Approx. test rows |
|---|---|---|
| Prevention (does it burn, how fast does it spread) | BASS (PSI-26), BASS-II (PSI-25), Saffire-I (PSI-98), Saffire-II (PSI-99), Saffire-III (PSI-100), ACME BRE (PSI-20) | ~250 BASS, ~20 Saffire, 18 BRE |
| Suppression (how flames go out) | FLEX (PSI-69), FLEX-2 (PSI-68), CFI (PSI-39) | 274, 8, 87 |
| Detection (catching it early) | SAME (PSI-102), SAME-R (PSI-101), DAFT / DAFT-2 (PSI-47) | 8, 109, 2 |
| Basic flame science | SPICE (PSI-107), SLICE (PSI-106), ACME CLD (PSI-21), Flame Design (PSI-10), s-Flame (PSI-23), E-FIELD (PSI-22), CFI-G (PSI-159) | 469, 12, 32, ~330, 18, 32, ~1,200 |
| Modelling (ground studies using flight data, text only) | PSI-62 (BASS spread), PSI-115 (SAME smoke), PSI-117 and PSI-142 (cool flames), PSI-60 (SPICE soot) | text only (PSI-142: 8) |

Treat counts as approximate and recompute from the data.

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

## 4. Tech stack

Everything is Python so it can be built and deployed in a day.

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Data fetch | `requests` |
| Data handling | `pandas` |
| LLM (tags, summaries, column mapping, Q&A) | Gemini or Azure OpenAI, **structured JSON output**. Key in `.env`, never committed |
| Q&A retrieval | `sentence-transformers` embeddings + FAISS (fallback: NumPy cosine similarity if FAISS fails to deploy) |
| Ranking | plain Python, transparent weighted score |
| Charts | Plotly |
| App | Streamlit (multipage) |
| Hosting | Streamlit Community Cloud (fallback: Hugging Face Spaces) |

**Hard rule:** all LLM outputs (tags, summaries, mappings) are generated once, saved to files and committed. The deployed app must run with **no API key**, except the Ask page, which degrades to keyword search if the API fails.

Pin versions in `requirements.txt` before the first deploy.

---

## 5. Repo layout

```
cool-flames/
  CLAUDE.md               this file
  SCHEMA.md               the data contract (section 6), source of truth
  README.md               what it is, how to run, data sources with DOIs, AI-use note, disclaimer
  requirements.txt        pinned
  .env.example            LLM_PROVIDER=, LLM_API_KEY=, LLM_MODEL=
  .gitignore              .env, __pycache__, .venv, *.pyc
  app/                    Streamlit (Ramneek)
    Home.py               landing page, sidebar habitat picker, disclaimer footer
    pages/
      1_Overview.py
      2_Scenario.py
      3_Gap_map.py
      4_Compare.py        stretch
      5_Ask.py            stretch
      6_Earth_benefits.py stretch
    components/           shared UI helpers (cards, warning cards, DOI links)
  core/                   pure logic, no Streamlit imports (Malay)
    scenarios.py          habitat presets, scenarios, phases
    ranking.py            score functions
    warnings.py           warning card rules
    loaders.py            load tests.csv / investigations.json (used by app)
  pipeline/               offline data build (Malay)
    fetch_psi.py          downloads all investigations to data/raw/
    units.py              unit conversions
    build_tests.py        merges mapped tables into data/clean/tests.csv
    build_ranges.py       per-investigation ranges to data/clean/ranges.csv
    mappings/             one JSON per table: source column -> schema column
  ai/                     offline AI build + Q&A (Ramneek)
    tag_summarize.py      writes data/ai/investigations.json
    map_columns.py        LLM proposes mappings into pipeline/mappings/ (reviewed by hand)
    build_index.py        chunks + embeddings into data/ai/index/
    qa.py                 retrieval + answer with DOI citations, keyword fallback
  data/
    raw/                  as fetched, committed
    clean/                tests.csv, ranges.csv
    ai/                   investigations.json, index/
    manual/               earth_vs_space.csv (hand-curated from papers)
    fake/                 stub data so the app can be built before real data lands
  tests/                  pytest: units, ranking, schema checks
```

`core/` must not import Streamlit, so it can be tested and reused. `app/` imports from `core/` and reads files from `data/`. The app never calls the PSI endpoint.

---

## 6. Data contract (mirror this in SCHEMA.md)

### 6.1 `data/clean/tests.csv`, one row per test run, all investigations

| Column | Type | Notes |
|---|---|---|
| `psi_id` | str | e.g. `PSI-99` |
| `run_id` | str | original run label, or row index if none |
| `fuel` | str | e.g. PMMA, heptane, ethylene, SIBAL |
| `fuel_phase` | enum | `solid`, `liquid`, `gas` |
| `fuel_class` | enum | `cabin_material`, `idealized` |
| `o2_pct` | float | % by volume (mole fraction x 100) |
| `pressure_psi` | float | converted from atm, kPa, mmHg |
| `ppo2_psi` | float | `o2_pct / 100 * pressure_psi` |
| `diluent` | str | `N2`, `He`, `CO2`, `mixed`; blank if unknown |
| `airflow_cms` | float | cm/s; blank if not reported |
| `sample_size_mm` | float | largest dimension; blank if not reported |
| `outcome` | enum | `burned`, `extinguished`, `no_ignition`, `unknown` |
| `metric_name` | str | main measurement, e.g. `spread_rate` |
| `metric_value` | float | its value |
| `metric_unit` | str | its unit, e.g. `mm/s` |
| `mapping_confidence` | enum | `hand`, `llm_checked`, `llm_unchecked` |

Rules:
- **Blank means "not reported". Never fill blanks with 0.** Zero airflow is a real test condition (BASS-II varied flow 0 to 55 cm/s).
- One main metric per row. If a table has several, keep the most fire-safety-relevant one (spread rate > burning rate > extinction time > others) and note the choice in the mapping file.
- Enums are lowercase exactly as listed. Validate them in `tests/`.
- Rows whose O2 or pressure cannot be determined are kept, but excluded from the gap map.

### 6.2 `data/ai/investigations.json`, list of objects, one per investigation

```json
{
  "psi_id": "PSI-99",
  "name": "Saffire-II",
  "doi": "10.xxxx/xxxx",
  "area": "prevention",
  "fuel_types": ["solid"],
  "hardware": "Cygnus",
  "platform": "Cygnus (post-ISS)",
  "summary_3line": "Line 1. Line 2. Line 3.",
  "key_findings": ["...", "..."],
  "n_runs": 9,
  "n_publications": 4,
  "o2_range": [21.0, 21.0],
  "pressure_range": [14.7, 14.7],
  "airflow_range": [20.0, 25.0],
  "test_scale": "large"
}
```

- `area` enum: `prevention`, `suppression`, `detection`, `basic`, `modelling`.
- Ranges are `[min, max]` two-number lists, or `null` if unknown. Computed from tests.csv, not from the LLM.
- `test_scale` enum: `large` (Saffire), `orbital` (ISS rack/glovebox), `ground`.
- Values in the example are placeholders. Never invent DOIs; copy them from the raw PSI record.

### 6.3 `data/manual/earth_vs_space.csv`, hand-curated

Columns: `material`, `measure`, `value_1g`, `value_ug`, `unit`, `finding`, `source`, `source_url`.
Example row: `PMMA, limiting O2 for flame spread, 18, 17, % O2, burns at lower O2 in microgravity, Flame spread over PMMA in microgravity (Scientific Reports 2018), <url>`.
Every row needs a source. Do not add rows from memory.

### 6.4 Unit conversions (`pipeline/units.py`)

- 1 atm = 14.696 psi
- 1 kPa = 0.14504 psi
- 1 mmHg = 0.019337 psi
- 1 bar = 14.504 psi
- mole fraction 0.21 = 21 % (if value <= 1.0 and the column is a fraction, multiply by 100)

Write unit tests with at least 5 known values. Flag (do not silently drop) any row whose computed `ppo2_psi` falls outside 0.5 to 16 psi.

### 6.5 Fake data (`data/fake/`)

10 rows of `tests.csv` covering all enums and a few blanks, and 3 entries of `investigations.json` (one prevention, one suppression, one detection). The app reads `data/clean/` and `data/ai/` if present, otherwise falls back to `data/fake/` and shows a small "demo data" badge.

---

## 7. Pipeline steps (Malay)

1. `fetch_psi.py`: download all investigations and tables to `data/raw/` (JSON + CSV). Idempotent; skip files that exist unless `--force`.
2. Inventory: write `data/raw/columns.md` listing each table's columns and units.
3. Hand-map the 5 core tables first: FLEX, BASS, BASS-II, Saffire-II, SAME-R. One JSON per table in `pipeline/mappings/`:
   ```json
   {
     "psi_id": "PSI-25",
     "table": "<file name>",
     "columns": {"O2 (%)": "o2_pct", "Pressure (kPa)": {"to": "pressure_psi", "unit": "kPa"}},
     "constants": {"fuel_phase": "solid", "fuel_class": "cabin_material"},
     "metric": {"source": "Spread rate (mm/s)", "name": "spread_rate", "unit": "mm/s"},
     "mapping_confidence": "hand",
     "notes": "why choices were made"
   }
   ```
4. `build_tests.py`: apply mappings, convert units, compute `ppo2_psi`, write `data/clean/tests.csv`.
5. LLM proposes mappings for the remaining tables (`ai/map_columns.py`), a human reviews each, sets `mapping_confidence`.
6. Spot-check 20 random rows against raw CSVs.
7. `build_ranges.py`: per-investigation ranges and run counts to `data/clean/ranges.csv`; merged into `investigations.json`.

Fallback if time runs out: ship with the 5 core tables only and label the rest "not yet standardized".

---

## 8. Scenarios and ranking (Malay, `core/`)

### 8.1 Scenarios (`core/scenarios.py`)

Each scenario has phases. Each phase maps to a fire-safety area.

| Scenario key | Label | Phases (in order) | Relevant fuel phases |
|---|---|---|---|
| `electrical_overheat` | Electrical overheat (wiring, avionics) | smoke, ignition, spread, suppression | solid |
| `cabin_material_fire` | Cabin material fire (fabric, plastics) | ignition, spread, suppression | solid |
| `liquid_leak` | Liquid leak (lubricant, cleaning fluid) | ignition, spread, suppression | liquid |
| `gas_leak` | Gas leak (O2 or fuel line) | ignition, spread, suppression | gas |
| `oxygen_rich_cabin` | Oxygen-rich cabin (Apollo 1 type) | ignition, spread, suppression | solid, gas |
| `lunar_dust` | Lunar dust and detectors | smoke | none (detection only) |

Phase to area: `smoke` -> `detection`; `ignition` -> `prevention`; `spread` -> `prevention`; `suppression` -> `suppression`. Investigations with area `basic` get partial area credit (0.5).

Historical context for the UI (static text): Apollo 1 (1967, pure-O2 cabin, pre-launch test), Apollo 13 (1970, oxygen tank failure), Mir (1997, oxygen generator fire). All three involved extra oxygen, the condition planned for the Moon Base.

### 8.2 Ranking score (`core/ranking.py`)

```
score = w1 * area_match + w2 * condition_overlap + w3 * fuel_realism + w4 * data_richness
```

Default weights: `w1=0.35, w2=0.30, w3=0.20, w4=0.15`. The app exposes them as sliders. Each component is in [0, 1].

- **area_match:** 1.0 if the investigation's `area` equals the phase's area; 0.5 if `basic`; else 0. Also multiply by 0 if none of the investigation's `fuel_types` is relevant to the scenario (except detection phases, which ignore fuel type).
- **condition_overlap:** distance from the habitat point to the **nearest test run** of that investigation, in normalized space: `dx = (o2_pct - h_o2) / 100`, `dy = (pressure_psi - h_p) / 14.7`, `d = sqrt(dx^2 + dy^2)`. `overlap = max(0, 1 - d / 0.5)`. Runs without O2 or pressure are ignored; if none remain, overlap = 0 and mark "conditions not reported".
- **fuel_realism:** `cabin_material` = 1.0; liquid or solid `idealized` = 0.6; idealized gas burner = 0.3. Use the investigation's dominant `fuel_class`.
- **data_richness:** `min(1, log10(1 + n_runs) / 3) * 0.7 + min(1, n_publications / 10) * 0.3`. Boost `test_scale == "large"` by +0.2, capped at 1.

Return for each investigation: total score, the four components, and a one-sentence explanation built from a template (no LLM), for example:
"Ranked 1st: detection study of smoke from overheated wire insulation; nearest test at 21% O2 / 14.7 psi; 109 runs."

Sanity check (must pass): habitat `moon_brief` + scenario `electrical_overheat`, phase `smoke` ranks SAME and SAME-R at the top.

### 8.3 Warning cards (`core/warnings.py`)

| Rule | When | Card text (gist) |
|---|---|---|
| No data yet | habitat is Moon or Mars / partial gravity | No partial-gravity data in PSI. Microgravity and 1 g results bound the in-between. FM2 and LUCI will add data. |
| Hidden hazard | liquid fuel and phase = suppression | Cool flames: FLEX droplets kept burning invisibly after the visible flame went out. |
| Detector blind spot | scenario = electrical_overheat and phase = smoke | ISS detector often missed small smoke particles from Teflon and Kapton (SAME, SAME-R; Meyer et al. 2018). |
| Earth tests not conservative | any solid-fuel scenario | Some materials burn at lower O2 in microgravity than on Earth (BASS PMMA 17% vs 18%). |
| Outside tested range | habitat O2 or pressure outside all tested runs of the top-ranked investigations | Nearest test is X O2 points / Y psi away. |

Return a list of `{level, title, body, sources}`; the app renders them.

---

## 9. App pages (Ramneek, `app/`)

Sidebar on every page: habitat picker (4 presets), disclaimer line. Footer: "Research and reference tool, not an operational safety system. Data: NASA PSI (CC0)."

| Page | Content | Status |
|---|---|---|
| Overview | One card per investigation: name, `summary_3line`, area badge, fuel types, O2 / pressure / airflow ranges, run count, DOI link. Filters by area and fuel phase. | MVP |
| Scenario Explorer | Pick scenario. Tabs per phase. Ranked list with score breakdown (bar of four components) and the one-sentence explanation. Weight sliders. Warning cards from `core/warnings.py`. | MVP |
| Gap map | Plotly scatter: every test run, x = pressure_psi, y = o2_pct, colour by area, hover shows psi_id, run_id, fuel, DOI. Habitat presets as large labelled markers. Dashed iso-ppO2 lines (curves o2_pct = 100 * ppO2 / pressure_psi) for 2.8, 3.1 and 4.3 psi. CSV download of tests.csv. | MVP |
| Compare | 2 to 4 investigations side by side: fuels, conditions, sensors, what varied. | stretch |
| Ask | Q&A answered only from investigation texts, every answer cites DOIs. Keyword fallback. | stretch |
| Earth benefits | Static: water-mist extinguishers, smoke detectors, firefighter gear. | stretch |

Cut order if behind: Earth benefits, Ask, Compare.

---

## 10. AI layer (Ramneek, `ai/`)

1. **Tag and summarize** (`tag_summarize.py`): for each investigation, send objective, approach, hypothesis, impacts and publication titles. Ask for JSON: `area`, `fuel_types`, `summary_3line`, `key_findings` (max 4, each one sentence, grounded in the text). Validate against the schema; retry once on invalid JSON. Save to `data/ai/investigations.json`. A human reads every summary once.
2. **Column mapping** (`map_columns.py`): given a table's column names and 5 sample rows, propose a mapping JSON in the format of section 7. Output goes to `pipeline/mappings/` with `mapping_confidence: llm_unchecked`; a human reviews.
3. **Q&A** (`build_index.py`, `qa.py`): chunk investigation texts (about 500 tokens, overlap 50), embed, index. At query time, retrieve top 5, answer only from them, cite DOIs. If retrieval score is low, say the data does not cover it. If the API fails, return the top keyword matches with their DOIs.

Prompts live in `ai/prompts/` as text files. No API calls at import time.

---

## 11. Conventions

- Python 3.11, type hints on public functions, docstrings one line where obvious.
- `pathlib` for paths. Paths relative to the repo root via a single `ROOT` constant in `core/loaders.py`.
- Pure functions in `core/`; side effects only in `pipeline/`, `ai/` and `app/`.
- Cache data loading in the app with `st.cache_data`.
- Small commits to `main`. Commit messages: `area: what changed` (e.g. `pipeline: map BASS-II table`).
- Tests with `pytest`: units, ranking sanity check, enum and column validation of tests.csv.
- Never commit `.env` or API keys.
- Do not add packages without need; keep the deploy small.
- Do not fabricate data, DOIs, numbers or citations. If a value is unknown, leave it blank and say so.

---

## 12. Task list with dependencies

The live tracker is the team's Claude Sheets board. IDs match.

| ID | Task | Owner | Depends on |
|---|---|---|---|
| K1 | Create repo with this layout | Malay | |
| K2 | Agree schema, write SCHEMA.md | Both | |
| K3 | Confirm deadline and team registration | Ramneek | |
| K4 | LLM API key in `.env` | Ramneek | |
| K5 | Fake data in `data/fake/` | Malay | K1, K2 |
| D1 | Run fetch_psi.py, commit data/raw/ | Malay | K1 |
| D2 | Inventory columns and units | Malay | D1 |
| D3 | units.py + tests | Malay | K1, K2 |
| D4 | Hand-map 5 core tables | Malay | D2, D3 |
| D5 | build_tests.py -> tests.csv | Malay | D4 |
| D6 | LLM mappings for other tables, review | Malay | D5, K4, A5 |
| D7 | Spot-check 20 rows | Malay | D6 |
| D8 | Ranges and run counts | Malay | D7 |
| R1 | scenarios.py | Malay | K2 |
| R2 | ranking.py | Malay | R1, K5 |
| R3 | Ranking sanity check on real data | Malay | R2, D5 |
| R4 | earth_vs_space.csv | Malay | K1 |
| R5 | warnings.py | Malay | R1 |
| A1 | Tag/summary prompt, test on 3 | Ramneek | D1, K4 |
| A2 | Run on all 24, save JSON | Ramneek | A1 |
| A3 | Q&A index | Ramneek | D1 |
| A4 | Q&A function with citations + fallback | Ramneek | A3, K4 |
| A5 | Column-mapping prompt for D6 | Ramneek | A1 |
| P1 | App skeleton | Ramneek | K1 |
| P2 | Overview page | Ramneek | P1, K5 |
| P3 | Scenario Explorer | Ramneek | P1, R2 |
| P4 | Gap map | Ramneek | P1, D5 |
| P5 | Warning cards in UI | Ramneek | P3, R5 |
| P6 | CSV download | Ramneek | P1, D5 |
| P7 | Compare page (stretch) | Malay | P2, D8 |
| P8 | Ask page (stretch) | Ramneek | P1, A4 |
| P9 | Earth benefits (stretch) | Malay | P1 |
| S1 | First deploy | Ramneek | P2, A2, D5 |
| S2 | Test public link (private window, phone) | Malay | S1 |
| S3 | README | Malay | S1 |
| S4 | Demo script | Both | P3, P4 |
| S5 | Record demo video | Both | S4, S1 |
| S6 | Submission form, DOIs, AI-use note | Ramneek | S3 |
| S7 | Final check and submit | Both | S2, S5, S6 |

---

## 13. Demo story (what the app must show well)

1. Hook: Apollo 1, Apollo 13 and Mir all involved extra oxygen; the Moon Base plans 30%+ O2.
2. Overview: 24 investigations, about 2,900 test runs, summarized and tagged.
3. Scenario: Moon rover + electrical overheat. Smoke phase ranks SAME / SAME-R first with the detector blind-spot warning. Move a slider to show why.
4. Gap map: habitat markers sit where almost no tests exist; ppO2 lines explain the higher fire risk.
5. No data yet: partial gravity is untested; FM2 and LUCI will fill it.
6. Close: CSV export for modellers, every claim tied to a DOI, research tool disclaimer.

Other public teams already show a basic gap map and mission views. Our edge is the **phase-by-phase scenario ranking with explanations**, the **detector blind-spot story** for electrical overheat, and the **ppO2 framing**. Make those clear and polished.

---

## 14. Key references (for README and warning card sources)

- Urban et al. 2019, Flame spread: effects of microgravity and scale, Combustion and Flame 199 (Saffire-I/II)
- Jomaas et al. 2015, Fire safety in space: beyond flammability testing of small samples, Acta Astronautica 109
- Combustion of solids in microgravity: BASS-II results (NTRS 2016)
- Flame spread over PMMA in microgravity, Scientific Reports 2018 (BASS)
- Olson 2004, Why NASA's current Test 1 might not always be conservative (NTRS)
- Ferkul, Kralik, Liao 2026, Material flammability at lunar and Martian gravity (LPSC) (FM2)
- Nayagam et al. 2012, Can cool flames support quasi-steady alkane droplet burning?, Combustion and Flame 159 (FLEX)
- Dietrich et al. 2014, Droplet combustion experiments aboard the ISS, Microgravity Sci. Technol. (FLEX)
- Urban et al. 2009, Smoke particle sizes in low-gravity, SAE (SAME)
- Meyer et al. 2018, Spacecraft smoke detector performance in low gravity, Fire Safety Journal (SAME, SAME-R)
- Impacts of reduced-pressure atmospheres on ECLSS (NTRS 2026)

Links: PSI repository `https://psi.nasa.gov/physci/repo`; NTRS API `https://ntrs.nasa.gov/api/citations/search`.

---

## 15. How Claude Code should work on this repo

- Start by reading `SCHEMA.md` and inspecting `data/raw/` before writing any parser.
- Ask which task ID you are working on; stay inside that owner's folders.
- After changing data code, run `pytest` and print the first 5 rows of the output file.
- After changing the app, run `streamlit run app/Home.py` locally and check each page loads with fake data and with real data.
- If a PSI table is ambiguous (unclear units, unclear outcome), stop and ask rather than guess.
- Keep the app working at every commit: the team may deploy at any moment.

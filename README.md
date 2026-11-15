# Cool Flames: Fire Scenario Explorer

NASA Space Apps Challenge 2026: *Flame in Freefall: SI-Powered Fire Safety Insights from
Microgravity Combustion Data*.

Pick a **habitat** (ISS, Moon base, NASA exploration habitat, spacesuit) and a **fire
scenario** (electrical overheat, cabin material fire, liquid leak, gas leak, oxygen-rich
cabin, lunar dust). The dashboard ranks NASA's microgravity combustion investigations for
each phase of that fire, explains every score, shows how close their test conditions come to
the habitat's atmosphere, and flags where **no data exists**.

> **Research and reference tool, not an operational safety system.** It reports what tests
> show and where data is missing; it never certifies a material or atmosphere.
> Data: NASA Physical Sciences Informatics (PSI), CC0.

## What is in the app

| Page | What it shows |
|---|---|
| **Investigations** | One card per investigation (24): AI summary, fire-safety area, fuels, O₂ / pressure / airflow ranges, runs, DOI. Filters and search. "Earth vs space" cards of sourced findings. |
| **Scenario Explorer** | Habitat + scenario → phase tabs (smoke, ignition, spread, suppression) → ranked investigations with a score breakdown, weight sliders and warning cards (detector blind spot, cool-flame hidden hazard, no partial-gravity data, Earth tests not conservative, outside tested range). |
| **Gap map** | Every standardized run with O₂ and pressure on one chart, habitat atmospheres on top, curves of equal O₂ partial pressure, and a CSV download of the standardized test table. |
| **Compare** | 2 to 4 investigations side by side: conditions, fuels, what varied, outcomes, main measurement. |
| **Ask** | Questions answered only from the PSI record texts, citing DOIs. Works without an API key (shows the source passages). |
| **Earth benefits** | What the records themselves say their results mean on Earth, quoted with DOIs. |

Key numbers: 24 investigations, about 2,000 test runs in the PSI tables, 1,858 runs
standardized from 19 tables into one schema, 1,009 of them with both O₂ and pressure
reported. Only 64 standardized runs sit near the Moon base atmosphere (30% O₂, 10.2 psi),
versus 341 near the ISS.

## Run locally

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app/Home.py
pytest
```

The app needs **no API key**: all AI outputs are generated offline and committed. For
written answers on the Ask page, add a free Google AI Studio key to `.env` (see
`.env.example`) or to Streamlit secrets:

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "a Flash model listed as free in AI Studio"
```

## Rebuild the data (optional; outputs are committed)

```bash
python pipeline/fetch_psi.py                 # 24 PSI records + 22 tables -> data/raw/
python -m pipeline.build_tests               # mappings -> data/clean/tests.csv
python -m pipeline.spot_check                # compare 20 cleaned rows with the raw tables
python -m pipeline.build_ranges              # -> data/clean/ranges.csv
python ai/tag_summarize.py --import data/ai/ai_fields.json   # -> data/ai/investigations.json
python ai/build_index.py                     # -> data/ai/index/ (Ask page)
```

Data rules (see `SCHEMA.md`, `pipeline/mappings/_FORMAT.md` and the change log in `TASKS.md`):

- **Blank means not reported, never 0.** Units are converted to psi and % O₂ in one place.
- **Pressure is never assumed.** Tables without a pressure column (BASS-II, Saffire, SAME,
  SPICE, the ACME day logs) stay blank and are left off the gap map.
- **Lists are not collapsed.** Cells such as `21; 26.5; 40` (several test conditions in one
  row) are left blank rather than reduced to one misleading value.
- Unphysical values (zero pressure, negative airflow) are blanked and flagged; real extremes
  (CFI-G up to 85% O₂ at 3.3 bar) are kept and flagged.

## Layout

- `app/`: `Home.py` (entry point and navigation), `views/` (one file per page), `components/` (shared UI), `static/` (logo). Theme: `.streamlit/config.toml`.
- `core/`: pure logic, no Streamlit: habitats and scenarios, ranking, warnings, loaders.
- `pipeline/`: offline data build from `data/raw/` to `data/clean/`.
- `ai/`: offline summaries, Q&A index and Q&A.
- `data/`: `raw/` (as fetched), `clean/`, `ai/`, `manual/earth_vs_space.csv`, `fake/`.
- `tests/`: unit, schema, ranking, warnings and Q&A tests.

## How the ranking works

`score = 0.35·area_match + 0.30·condition_overlap + 0.20·fuel_realism + 0.15·data_richness`
(weights adjustable in the app). Area match compares the study's fire-safety area with the
phase; condition overlap is the distance from the habitat to the study's nearest tested
O₂/pressure point; fuel realism favours real cabin materials over idealized burners; data
richness counts runs and publications, with a bonus for large-scale tests. Explanations are
templates, not AI text. Check: for Moon base + electrical overheat, the smoke phase ranks
SAME-R and SAME first.

## Data sources

All data comes from NASA's [Physical Sciences Informatics](https://psi.nasa.gov/) repository
(public, CC0). Each investigation is cited by its DOI, as PSI requires.

| PSI ID | Investigation | Area | DOI |
|---|---|---|---|
| PSI-10 | ACME / Flame Design | basic | [10.60555/w4zy-bt45](https://doi.org/10.60555/w4zy-bt45) |
| PSI-20 | ACME Burning Rate Emulator (BRE) | prevention | [10.60555/vb93-3y72](https://doi.org/10.60555/vb93-3y72) |
| PSI-21 | ACME Coflow Laminar Diffusion Flame (CLD) | basic | [10.60555/23e1-9950](https://doi.org/10.60555/23e1-9950) |
| PSI-22 | ACME E-FIELD Flames | basic | [10.60555/se5a-8c73](https://doi.org/10.60555/se5a-8c73) |
| PSI-23 | ACME s-Flame | basic | [10.60555/k57n-p030](https://doi.org/10.60555/k57n-p030) |
| PSI-25 | BASS-II | prevention | [10.60555/4qc4-de67](https://doi.org/10.60555/4qc4-de67) |
| PSI-26 | BASS | prevention | [10.60555/58h4-dy80](https://doi.org/10.60555/58h4-dy80) |
| PSI-39 | Cool Flames Investigation (CFI) | suppression | [10.60555/m6pj-a914](https://doi.org/10.60555/m6pj-a914) |
| PSI-47 | DAFT / DAFT-2 | detection | [10.60555/ztgj-d202](https://doi.org/10.60555/ztgj-d202) |
| PSI-60 | Computational and Experimental Analysis of SPICE Data Sets | modelling | [10.60555/mzjm-yv57](https://doi.org/10.60555/mzjm-yv57) |
| PSI-62 | Concurrent Flame Spread Modeling (BASS comparison) | modelling | [10.60555/e9xp-ex83](https://doi.org/10.60555/e9xp-ex83) |
| PSI-68 | FLEX-2 | suppression | [10.60555/byp8-h018](https://doi.org/10.60555/byp8-h018) |
| PSI-69 | Flame Extinguishment Experiment (FLEX) | suppression | [10.60555/mbq8-0451](https://doi.org/10.60555/mbq8-0451) |
| PSI-98 | SAFFIRE-I | prevention | [10.60555/0t15-1z43](https://doi.org/10.60555/0t15-1z43) |
| PSI-99 | SAFFIRE-II | prevention | [10.60555/2chp-m469](https://doi.org/10.60555/2chp-m469) |
| PSI-100 | SAFFIRE-III | prevention | [10.60555/040q-4h36](https://doi.org/10.60555/040q-4h36) |
| PSI-101 | SAME-R | detection | [10.60555/2np7-jv14](https://doi.org/10.60555/2np7-jv14) |
| PSI-102 | SAME | detection | [10.60555/gd4k-8h62](https://doi.org/10.60555/gd4k-8h62) |
| PSI-106 | SLICE | basic | [10.60555/pm12-rg61](https://doi.org/10.60555/pm12-rg61) |
| PSI-107 | SPICE | basic | [10.60555/9kbh-e962](https://doi.org/10.60555/9kbh-e962) |
| PSI-115 | SAME smoke modelling and simulation | modelling | [10.60555/q0v5-1v28](https://doi.org/10.60555/q0v5-1v28) |
| PSI-117 | Cool flame dynamics under thermo-convective perturbation (CFD) | modelling | [10.60555/gz0q-b577](https://doi.org/10.60555/gz0q-b577) |
| PSI-142 | Cool flame transitions at radiation/stretch extinction | modelling | [10.60555/80qf-vj95](https://doi.org/10.60555/80qf-vj95) |
| PSI-159 | ACME CFI-G (Cool Flames Investigation with Gases) | basic | [10.60555/cyt1-kh64](https://doi.org/10.60555/cyt1-kh64) |

Earth-vs-space findings (`data/manual/earth_vs_space.csv`) additionally cite: Link et al.
2018, *The Effect of Gravity on Flame Spread over PMMA Cylinders*, Scientific Reports
([doi:10.1038/s41598-017-18398-4](https://doi.org/10.1038/s41598-017-18398-4)); Olson 2004,
NASA/TM-2004-213114 ([NTRS 20040084156](https://ntrs.nasa.gov/citations/20040084156));
Nayagam, Dietrich, Hicks, Williams 2014, *Cool-flame extinction during n-alkane droplet
combustion in microgravity* ([NTRS 20140006750](https://ntrs.nasa.gov/citations/20140006750)).
Warning cards cite the papers listed in `core/warnings.py`.

## Use of AI

- **Summaries, fuel tags and key findings** for the 24 investigations were written by an AI
  assistant (Claude, Anthropic) from each PSI record's own text and publication titles only,
  then merged by `ai/tag_summarize.py`. DOIs, names, areas, conditions and run counts are
  copied from the PSI data, never generated. Each card links its DOI so a summary can be
  checked against the record.
- **Table standardization** (`pipeline/mappings/`) was written by hand with AI coding
  assistance and checked against the raw tables (`pipeline/spot_check.py`).
- **Ask page**: retrieval uses the open `all-MiniLM-L6-v2` embedding model with FAISS plus
  keyword matching; optional written answers use Google Gemini (AI Studio), restricted to
  the retrieved passages and required to cite DOIs.
- **Ranking and warnings** are transparent rules, not AI.
- The code was written with help from AI coding assistants (Claude Code).

## License

Code: MIT (see `LICENSE`). Data: NASA PSI, CC0; cite each investigation by its DOI.

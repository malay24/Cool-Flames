# Space Apps 2026 submission text (draft)

Paste each section into the matching field of the project submission form. Replace the
three `[...]` links before submitting.

- **Project name:** Cool Flames: Fire Scenario Explorer
- **Challenge:** Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data
- **Demo video:** [VIDEO URL]
- **Live app:** [STREAMLIT APP URL]
- **Code:** [GITHUB REPO URL]

## High-level summary

Spacecraft fires behave differently from fires on Earth, and NASA's Moon base plans to run
at 30% oxygen, the kind of oxygen-rich atmosphere involved in Apollo 1, Apollo 13 and Mir.
Cool Flames turns NASA's 24 microgravity combustion investigations (Physical Sciences
Informatics, about 2,000 test runs) into a Fire Scenario Explorer. A researcher picks a
habitat and a fire scenario; the dashboard ranks the investigations that matter for each
phase of the fire (smoke, ignition, spread, suppression), explains every score, shows how
close the tested oxygen and pressure come to that habitat, and flags what no test covers,
such as partial gravity. AI summarizes every investigation and answers questions only from
NASA's records, always citing DOIs. It is a research and reference tool, not an operational
safety system.

## Project details

**What it does**

- **Overview:** one card per investigation with an AI summary, fire-safety area, fuels,
  tested O₂ / pressure / airflow ranges and DOI, plus an "Earth vs space" table of sourced
  findings showing where normal-gravity tests understate (and in one case overstate) burning
  in microgravity.
- **Scenario Explorer:** transparent weighted ranking (area match, closeness of tested
  conditions, fuel realism, data richness) with adjustable weights, and warning cards: the ISS
  smoke detector's blind spot for Teflon and Kapton smoke, "cool flames" that keep liquid
  fuel burning invisibly, Earth tests that are not conservative, and the absence of
  partial-gravity data.
- **Gap map:** 1,009 runs plotted by pressure and oxygen with the ISS, Moon base,
  exploration habitat and spacesuit atmospheres and curves of equal oxygen partial pressure.
  Only 64 runs sit near the Moon base atmosphere (341 near ISS air, none near a spacesuit).
- **Compare** 2 to 4 investigations, **Ask** cited questions, and **Earth benefits** quoted
  from the records.
- **Data for modellers:** 1,858 runs from 19 differently shaped NASA tables standardized
  into one schema (units in psi and % O₂, blanks never filled with zeros, pressure never
  assumed), downloadable as CSV.

**Benefits:** researchers and students see in minutes which NASA experiments apply to a
habitat and fire, how far the data is from that habitat, and what still needs testing (for
example, the upcoming FM2 and LUCI partial-gravity experiments).

**Tools:** Python, pandas, Streamlit, Plotly, sentence-transformers + FAISS (retrieval),
Google Gemini via AI Studio (optional written answers), pytest. Hosted on Streamlit
Community Cloud.

## NASA data used

All 24 combustion investigations in NASA's Physical Sciences Informatics (PSI) repository,
public and CC0, each cited by DOI: ACME Flame Design (10.60555/w4zy-bt45), ACME BRE
(10.60555/vb93-3y72), ACME CLD Flame (10.60555/23e1-9950), ACME E-FIELD Flames
(10.60555/se5a-8c73), ACME s-Flame (10.60555/k57n-p030), BASS-II (10.60555/4qc4-de67), BASS
(10.60555/58h4-dy80), CFI (10.60555/m6pj-a914), DAFT / DAFT-2 (10.60555/ztgj-d202), PSI-60
SPICE data analysis (10.60555/mzjm-yv57), PSI-62 concurrent flame spread modeling
(10.60555/e9xp-ex83), FLEX-2 (10.60555/byp8-h018), FLEX (10.60555/mbq8-0451), SAFFIRE-I
(10.60555/0t15-1z43), SAFFIRE-II (10.60555/2chp-m469), SAFFIRE-III (10.60555/040q-4h36),
SAME-R (10.60555/2np7-jv14), SAME (10.60555/gd4k-8h62), SLICE (10.60555/pm12-rg61), SPICE
(10.60555/9kbh-e962), PSI-115 SAME smoke modelling (10.60555/q0v5-1v28), PSI-117 cool flame
CFD (10.60555/gz0q-b577), PSI-142 cool flame transitions (10.60555/80qf-vj95), ACME CFI-G
(10.60555/cyt1-kh64). Source: https://psi.nasa.gov/

## Use of artificial intelligence

- The 3-line summaries, fuel tags and key findings for each investigation were written by an
  AI assistant (Claude, Anthropic) from the PSI record text and publication titles only.
  DOIs, names, areas, test conditions and run counts come from NASA's data, not from AI.
- The Ask page retrieves passages with the open all-MiniLM-L6-v2 embedding model and FAISS;
  if configured, Google Gemini writes an answer restricted to those passages and citing DOIs.
  Without a key it shows the passages themselves.
- Code, data mappings and documents were written with help from AI coding assistants
  (Claude Code) and checked by the team; the ranking and warning rules are transparent code,
  not AI.

## References

- NASA Physical Sciences Informatics: https://psi.nasa.gov/
- Link et al. 2018, The Effect of Gravity on Flame Spread over PMMA Cylinders, Scientific
  Reports, https://doi.org/10.1038/s41598-017-18398-4
- Olson 2004, Most Probable Fire Scenarios in Spacecraft and Extraterrestrial Habitats: Why
  NASA's Current Test 1 Might Not Always Be Conservative, NASA/TM-2004-213114,
  https://ntrs.nasa.gov/citations/20040084156
- Nayagam, Dietrich, Hicks, Williams 2014, Cool-flame extinction during n-alkane droplet
  combustion in microgravity, https://ntrs.nasa.gov/citations/20140006750

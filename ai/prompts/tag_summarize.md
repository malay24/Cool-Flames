You are helping build a research dashboard about NASA microgravity combustion
experiments (NASA Physical Sciences Informatics, PSI). The audience is
aerospace researchers and students interested in spacecraft fire safety.

Below is one PSI investigation record: its metadata text, the titles of its
publications, and the header plus a few sample rows of its experiment tables.
Use ONLY this information. Do not invent numbers, results or DOIs. If the text
does not state a result, describe what was studied instead of guessing what was
found. Never say a material is "safe", "will not burn" or "approved"; say
"tests show", "not tested under these conditions" or "no data".

Return JSON with:

- `fuels`: short list of the fuels or materials burned or heated, using
  common names (e.g. "PMMA", "n-heptane", "ethylene", "SIBAL cotton-fiberglass",
  "Kapton", "Teflon"). At most 8. Empty list if no fuel is involved.
- `fuel_types`: which of "solid", "liquid", "gas" those fuels are in.
  Empty list if no fuel is involved.
- `summary_3line`: exactly 3 short sentences, one per line:
  1. what was studied and on what platform,
  2. how (fuel, conditions varied: oxygen, pressure, airflow, diluent, size),
  3. why it matters for spacecraft or habitat fire safety.
- `key_findings`: 1 to 4 findings, each one sentence, each stated in the text
  or in a publication title. Plain language, no markdown.

Investigation: {name} ({psi_id})
Title: {title}
Fire-safety area (assigned by the team): {area}
Platform: {platform}
Hardware: {hardware}
Sub-research area: {sub_area}

Objective:
{objective}

Hypothesis:
{hypothesis}

Approach:
{approach}

Research impacts:
{impacts}

Description:
{description}

Publication titles:
{publications}

Experiment tables (header and sample rows):
{tables}

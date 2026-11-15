# SCHEMA.md: Freefall Fire Atlas data contract

Source of truth for the data contract. Mirrors CLAUDE.md section 6. Changing any
column or enum here requires agreement from both owners (Malay and Ramneek).

Status: **signed**

## `data/clean/tests.csv` — one row per test run

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

Rules: blank means "not reported" — never fill blanks with 0. One main metric per
row (spread_rate > burning_rate > extinction_time > others). Enums lowercase
exactly. Rows missing O2 or pressure are kept but excluded from the gap map.

## `data/ai/investigations.json` — one object per investigation

See CLAUDE.md section 6.2 for the full example. `area` enum: `prevention`,
`suppression`, `detection`, `basic`, `modelling`. `test_scale` enum: `large`,
`orbital`, `ground`. Ranges are `[min, max]` or `null`; computed from tests.csv,
not the LLM. Never invent DOIs.

## `data/manual/earth_vs_space.csv` — hand-curated

Columns: `material`, `measure`, `flag`, `value_1g`, `value_ug`, `unit`, `finding`,
`source`, `source_url`. Every row needs a source. `flag` (added in R4) is a short
hand-written verdict shown in the app, e.g. "Burns at lower O2 in space" or
"Burned less in space (this sample)"; findings in both directions are kept.

## Unit conversions

1 atm = 14.696 psi; 1 kPa = 0.14504 psi; 1 mmHg = 0.019337 psi;
1 bar = 14.504 psi. Flag any computed `ppo2_psi` outside 0.5 to 16 psi.

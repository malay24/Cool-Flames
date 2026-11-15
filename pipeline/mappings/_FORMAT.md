# Mapping file format (D4/D6)

One JSON file per experiment table. `build_tests.py` (D5) consumes these to emit
`data/clean/tests.csv`. Extends the example in CLAUDE.md section 7.

```jsonc
{
  "psi_id": "PSI-99",
  "table": "PSI-99_Experimental table_SAFFIRE-2.csv",   // file in data/raw/tables/
  "columns": {
    // source header -> schema column, as a plain string...
    "Sample Number": "run_id",
    // ...or an object when a unit conversion is needed:
    "Percent O2 (Note 1)": {"to": "o2_pct", "unit": "pct"},
    "Air Flow (cm/s)":     {"to": "airflow_cms", "unit": "cms"}
  },
  "constants": {"fuel_phase": "solid", "fuel_class": "cabin_material"},
  "metric": {"source": "?-g Spread Length", "name": "spread_rate", "unit": "mm/s"},
  "outcome_from": {"source": "Burn Time (s)",
                   "map": {"Insignificant": "no_ignition"},
                   "default": "burned"},
  "diluent_from": {"N2": "N initial ambient composition; mole fraction",
                   "He": "He initial ambient composition; mole fraction",
                   "CO2": "CO initial ambient composition; mole fraction"},
  "mapping_confidence": "hand",
  "notes": "free text: why choices were made, known quirks"
}
```

## Conventions D5 must honour

- **Header matching:** D5 reads CSVs as `utf-8-sig` (strips BOM) and trims leading/
  trailing whitespace from headers before matching. Keys here use that trimmed form
  (internal double spaces and typos preserved, e.g. `Calibrated  initial O2 % by vol`).
- **Units** (`unit` field): `fraction` (×100 → %), `pct` (identity), `mmHg`/`kPa`/
  `atm`/`bar`/`psi` (→ psi via `units.py`), `cm` (×10 → mm), `mm`/`cms` (identity).
- **Messy numeric values:** D5 extracts the value from strings like `"~ 21.5"`,
  `"22.1 to 22.0"` (→ midpoint), `"20 cm/s"` (strip unit). `"n/a"`, `"Insignificant"`,
  `""` → blank. **Blank is never 0** (CLAUDE.md section 6.1).
- **`constants`:** fixed values applied to every row (may include `outcome`,
  `diluent`, etc.).
- **`outcome_from`:** map matched source values to the `outcome` enum; unmatched →
  `default` (omit `default` to leave blank).
- **`diluent_from`:** pick the diluent whose fraction column is largest for that row.
- **`metric`:** one main metric per row (spread_rate > burning_rate > extinction_time
  > others). Omit the key entirely if the table has no fire-safety metric.
- **Unmapped schema columns** are left blank, which means "not reported".

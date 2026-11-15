"""Unit conversions (CLAUDE.md section 6.4).

Task D3. 1 atm = 14.696 psi; 1 kPa = 0.14504 psi; 1 mmHg = 0.019337 psi;
1 bar = 14.504 psi. Mole fraction <= 1.0 in a fraction column -> *100 for %.
Flag (do not drop) rows whose ppo2_psi falls outside 0.5 to 16 psi.
"""

# TODO (D3): conversion functions + tests/test_units.py with >= 5 known values.

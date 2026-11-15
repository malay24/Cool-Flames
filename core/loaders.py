"""Load clean data for the app. Single source of the repo ROOT path.

Pure data access, no Streamlit imports (CLAUDE.md section 11). The app reads
data/clean/ and data/ai/ if present, otherwise falls back to data/fake/.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# TODO (D5/A2): load tests.csv and investigations.json with fake-data fallback.

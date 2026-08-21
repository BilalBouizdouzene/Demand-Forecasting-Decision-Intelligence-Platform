"""Download and validate the public M5 files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from demand_intelligence.config import PROJECT_ROOT, ensure_dirs
from demand_intelligence.data.download import acquire_m5
from demand_intelligence.logging_utils import configure_logging

if __name__ == "__main__":
    configure_logging()
    ensure_dirs()
    acquire_m5(PROJECT_ROOT / "data/raw", PROJECT_ROOT / "results/reports/data_acquisition.json")
    print("M5 raw files acquired and validated.")

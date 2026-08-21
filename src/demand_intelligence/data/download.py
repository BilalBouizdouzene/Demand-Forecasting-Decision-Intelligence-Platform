"""Reproducible M5 acquisition with authenticated and manual fallbacks."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)

REQUIRED_FILES = {
    "sales_train_validation.csv": ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"],
    "calendar.csv": ["date", "wm_yr_wk", "d", "weekday", "wday", "month", "year"],
    "sell_prices.csv": ["store_id", "item_id", "wm_yr_wk", "sell_price"],
}

# Zenodo exposes the original public files as individual downloads. The Kaggle
# route is preferred because it is the competition's canonical source.
ZENODO_URLS = {
    "sales_train_validation.csv": "https://zenodo.org/records/10203108/files/sales_train_validation.csv?download=1",
    "calendar.csv": "https://zenodo.org/records/10203108/files/calendar.csv?download=1",
    "sell_prices.csv": "https://zenodo.org/records/10203108/files/sell_prices.csv?download=1",
}


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    """Keep report paths portable and independent of the local checkout path."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def validate_raw_files(raw_dir: str | Path) -> dict[str, dict[str, object]]:
    """Validate existence, non-empty size, and required columns without loading sales values."""
    raw_path = Path(raw_dir)
    report: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for filename, required_columns in REQUIRED_FILES.items():
        path = raw_path / filename
        item: dict[str, object] = {"path": _display_path(path), "exists": path.exists()}
        if not path.exists():
            errors.append(f"Missing {path}")
            report[filename] = item
            continue
        item["size_bytes"] = path.stat().st_size
        item["sha256"] = _sha256(path)
        if path.stat().st_size == 0:
            errors.append(f"Empty file {path}")
            report[filename] = item
            continue
        header = pd.read_csv(path, nrows=0)
        missing = sorted(set(required_columns) - set(header.columns))
        item["columns"] = list(header.columns)
        item["missing_required_columns"] = missing
        if missing:
            errors.append(f"{filename} is missing columns: {missing}")
        report[filename] = item
    if errors:
        raise FileNotFoundError("Raw M5 validation failed: " + "; ".join(errors))
    return report


def _kaggle_available() -> bool:
    return bool(
        (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")) or os.getenv("KAGGLE_API_TOKEN")
    )


def _download_from_kaggle(raw_dir: Path) -> bool:
    if not _kaggle_available():
        return False
    command = [
        sys.executable,
        "-m",
        "kaggle",
        "competitions",
        "download",
        "-c",
        "m5-forecasting-accuracy",
        "-p",
        str(raw_dir),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        LOGGER.warning("Kaggle download did not complete: %s", exc)
        return False
    archives = sorted(raw_dir.glob("*.zip"))
    for archive in archives:
        try:
            shutil.unpack_archive(archive, raw_dir)
        except shutil.ReadError:
            LOGGER.warning("Unable to unpack %s", archive)
    return all((raw_dir / name).exists() for name in REQUIRED_FILES)


def _download_from_zenodo(raw_dir: Path) -> bool:
    for filename, url in ZENODO_URLS.items():
        target = raw_dir / filename
        if target.exists() and target.stat().st_size > 0:
            continue
        LOGGER.info("Trying public Zenodo download for %s", filename)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "demand-intelligence/0.1"})
            with (
                urllib.request.urlopen(request, timeout=60) as response,
                target.open("wb") as handle,
            ):
                shutil.copyfileobj(response, handle)
        except Exception as exc:  # pragma: no cover - depends on network availability
            LOGGER.warning("Zenodo download failed for %s: %s", filename, exc)
            if target.exists():
                target.unlink()
            return False
    return True


def acquire_m5(
    raw_dir: str | Path = "data/raw",
    report_path: str | Path = "results/reports/data_acquisition.json",
) -> dict[str, dict[str, object]]:
    """Acquire M5 or fail with exact manual placement instructions."""
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    try:
        report = validate_raw_files(raw_path)
    except FileNotFoundError:
        report = None
    if report is None:
        if not _download_from_kaggle(raw_path):
            _download_from_zenodo(raw_path)
        report = validate_raw_files(raw_path)
    output = Path(report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

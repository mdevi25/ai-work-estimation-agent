"""Shared JSON/CSV configuration loading for deterministic engines.

No engine may fall back to a silently hard-coded value when configuration
is missing or malformed -- every failure here raises ConfigurationError.
"""
import csv
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ConfigurationError(ValueError):
    """Raised when a required configuration file is missing or malformed."""


def load_json_config(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise ConfigurationError(f"Missing required configuration file: {filename}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in configuration file {filename}: {exc}"
        ) from exc


def load_csv_config(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        raise ConfigurationError(f"Missing required configuration file: {filename}")
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except csv.Error as exc:
        raise ConfigurationError(f"Invalid CSV in configuration file {filename}: {exc}") from exc

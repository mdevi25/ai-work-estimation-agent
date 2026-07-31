"""Relative Job Size, T-shirt size, and sprint-range mapping.

Owns: mapping the unrounded weighted complexity score to the configured
Relative Job Size band, T-shirt size, sprint range, and size-13/size-20
warnings.

Must not: calculate resource cost or price, or duplicate the weighted
complexity formula owned by complexity_engine.py.
"""
from __future__ import annotations

from src.config import load_json_config
from src.models import SizingResult
from src.validators import validate_sizing_bands


def load_sizing_bands() -> list[dict]:
    bands = load_json_config("sizing_bands.json")
    validate_sizing_bands(bands)
    return bands


def map_to_size(weighted_complexity_score: float) -> SizingResult:
    """Map the unrounded weighted complexity score to Relative Job Size,
    T-shirt size, and sprint range per COMPLEXITY-AND-SIZING.md section 5.

    Always uses the unrounded score, never the two-decimal display value.
    """
    bands = load_sizing_bands()

    for band in sorted(bands, key=lambda b: b["min_score"]):
        if band["min_score"] <= weighted_complexity_score <= band["max_score"]:
            return SizingResult(
                relative_job_size=band["relative_job_size"],
                tshirt_size=band["tshirt_size"],
                min_sprints=band["min_sprints"],
                max_sprints=band["max_sprints"],
                discovery_review_required=band["discovery_review_required"],
                decomposition_required=band["decomposition_required"],
            )

    raise ValueError(
        f"Weighted complexity score {weighted_complexity_score} does not fall within "
        "any configured sizing band"
    )

"""Non-authoritative "preliminary" sidebar preview, based on partially
answered complexity questions.

This module exists so the persistent sidebar can show something useful
before all seven complexity dimensions are answered, without ever treating
an unanswered dimension as a zero score and without touching the
authoritative engine. Per EAP.M1.UI1-D1 correction 2:

- Labeled "Preliminary" by the caller (this module returns the data; app.py
  renders the label).
- Shows how many of the seven dimensions are answered.
- Once all seven are answered, callers must switch to
  complexity_engine.calculate_weighted_complexity (the authoritative
  engine) rather than this module -- see app.py's Review/Generate step,
  which never calls this module.

Reuses the unmodified, approved sizing bands via sizing_engine.map_to_size
so the preliminary size still reflects the real governed mapping table --
only the complexity score feeding it is partial and re-normalized among
answered dimensions.
"""
from __future__ import annotations

from typing import Optional

from src.complexity_engine import load_complexity_weights
from src.models import COMPLEXITY_DIMENSION_KEYS, SizingResult
from src.sizing_engine import map_to_size


def compute_preliminary_view(dimension_scores: dict[str, int]) -> dict:
    """dimension_scores contains only the dimensions answered so far."""
    total_dimensions = len(COMPLEXITY_DIMENSION_KEYS)
    answered_count = len(dimension_scores)

    result: dict[str, object] = {
        "answered_count": answered_count,
        "total_dimensions": total_dimensions,
        "preliminary_score": None,
        "preliminary_sizing": None,
    }

    if answered_count == 0:
        return result

    weights = load_complexity_weights()
    answered_weight_total = sum(weights[key] for key in dimension_scores)
    if answered_weight_total <= 0:
        return result

    weighted_sum = sum(score * weights[key] for key, score in dimension_scores.items())
    # Re-normalize among answered dimensions only -- unanswered dimensions
    # are excluded from both numerator and denominator, never treated as 0.
    preliminary_score = weighted_sum / answered_weight_total
    result["preliminary_score"] = preliminary_score

    sizing: Optional[SizingResult] = None
    try:
        sizing = map_to_size(preliminary_score)
    except ValueError:
        sizing = None
    result["preliminary_sizing"] = sizing

    return result

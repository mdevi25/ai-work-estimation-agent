"""Weighted complexity calculation.

Owns: loading and validating complexity weights and questions, computing the
weighted complexity score at full precision, its two-decimal display value,
and explanatory per-dimension contribution data.

Must not: map Relative Job Size, T-shirt size, or sprint range (owned by
sizing_engine.py) or assign pricing.
"""
from __future__ import annotations

from src.config import load_json_config
from src.models import COMPLEXITY_DIMENSION_KEYS, ComplexityResult
from src.validators import validate_complexity_questions_schema, validate_dimension_score, validate_weight_total


def load_complexity_weights() -> dict[str, float]:
    weights = load_json_config("complexity_weights.json")
    validate_weight_total(weights)
    return weights


def load_complexity_questions() -> dict:
    questions = load_json_config("complexity_questions.json")
    validate_complexity_questions_schema(questions)
    return questions


def calculate_weighted_complexity(dimension_scores: dict[str, int]) -> ComplexityResult:
    """Compute the weighted complexity score per COMPLEXITY-AND-SIZING.md section 2.

    weighted_complexity_score = sum(dimension_score * dimension_weight)

    The full-precision value is preserved on the result; only the display
    string is rounded to two decimal places. Mapping decisions elsewhere
    must use the unrounded `weighted_complexity_score`, never the display
    string.
    """
    if set(dimension_scores.keys()) != set(COMPLEXITY_DIMENSION_KEYS):
        raise ValueError(
            f"dimension_scores must define exactly these dimensions: {sorted(COMPLEXITY_DIMENSION_KEYS)}"
        )

    weights = load_complexity_weights()

    validated_scores = {
        key: validate_dimension_score(score) for key, score in dimension_scores.items()
    }

    contributions = {key: validated_scores[key] * weights[key] for key in COMPLEXITY_DIMENSION_KEYS}
    weighted_score = sum(contributions.values())

    # "Higher-scoring complexity dimensions" per EAP.M1-D1 correction 2:
    # explanatory only, dimensions scoring 4 or 5. Does not create a
    # warning, threshold, status, or pricing rule -- display use only.
    higher_scoring_dimensions = sorted(
        (key for key in COMPLEXITY_DIMENSION_KEYS if validated_scores[key] >= 4),
        key=lambda key: (-validated_scores[key], key),
    )

    return ComplexityResult(
        dimension_scores=validated_scores,
        dimension_weights=weights,
        dimension_contributions=contributions,
        weighted_complexity_score=weighted_score,
        weighted_complexity_display=f"{weighted_score:.2f}",
        higher_scoring_dimensions=higher_scoring_dimensions,
    )

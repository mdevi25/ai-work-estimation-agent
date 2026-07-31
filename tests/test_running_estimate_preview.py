import pytest

from src.running_estimate_preview import compute_preliminary_view


def test_no_answers_yet_returns_no_score():
    result = compute_preliminary_view({})
    assert result["answered_count"] == 0
    assert result["total_dimensions"] == 7
    assert result["preliminary_score"] is None
    assert result["preliminary_sizing"] is None


def test_partial_answers_renormalize_among_answered_dimensions_only():
    # Only functional (weight 0.20) and technical (weight 0.20) answered,
    # both scored 4 -- the re-normalized preliminary score must equal 4,
    # not be dragged down by the unanswered dimensions' combined weight.
    result = compute_preliminary_view({"functional": 4, "technical": 4})
    assert result["answered_count"] == 2
    assert result["preliminary_score"] == pytest.approx(4.0)
    assert result["preliminary_sizing"] is not None


def test_partial_answers_never_treat_unanswered_as_zero():
    # If unanswered dimensions were silently treated as 0, a single answered
    # dimension scored 5 would produce a tiny weighted score. Re-normalized,
    # it must equal 5, not a small fraction of 5.
    result = compute_preliminary_view({"data": 5})
    assert result["preliminary_score"] == pytest.approx(5.0)


def test_all_seven_answered_matches_full_precision_style_result():
    scores = {
        "functional": 3,
        "technical": 3,
        "integration": 3,
        "data": 3,
        "testing": 3,
        "dependency": 3,
        "operational_risk": 3,
    }
    result = compute_preliminary_view(scores)
    assert result["answered_count"] == 7
    assert result["preliminary_score"] == pytest.approx(3.0)
    assert result["preliminary_sizing"].relative_job_size is not None

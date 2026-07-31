import pytest

from src.sizing_engine import map_to_size

BOUNDARY_CASES = [
    (0.00, 1, "XS", False, False),
    (0.75, 1, "XS", False, False),
    (0.76, 2, "S", False, False),
    (1.50, 2, "S", False, False),
    (1.51, 3, "S", False, False),
    (2.00, 3, "S", False, False),
    (2.01, 5, "M", False, False),
    (3.00, 5, "M", False, False),
    (3.01, 8, "L", False, False),
    (4.00, 8, "L", False, False),
    (4.01, 13, "XL", True, False),
    (4.60, 13, "XL", True, False),
    (4.61, 20, "Epic", False, True),
    (5.00, 20, "Epic", False, True),
]


@pytest.mark.parametrize("score,rjs,tshirt,discovery,decomposition", BOUNDARY_CASES)
def test_size_boundaries(score, rjs, tshirt, discovery, decomposition):
    result = map_to_size(score)
    assert result.relative_job_size == rjs
    assert result.tshirt_size == tshirt
    assert result.discovery_review_required is discovery
    assert result.decomposition_required is decomposition


def test_sprint_ranges_for_sizes_2_and_3_are_distinct_despite_same_tshirt():
    result_2 = map_to_size(1.00)
    result_3 = map_to_size(1.75)
    assert result_2.tshirt_size == result_3.tshirt_size == "S"
    assert (result_2.min_sprints, result_2.max_sprints) != (result_3.min_sprints, result_3.max_sprints)


def test_score_outside_range_raises():
    with pytest.raises(ValueError):
        map_to_size(5.5)
    with pytest.raises(ValueError):
        map_to_size(-0.5)

import pytest

from app.modules.profiles.maturity import MATURITY_LEVELS, allows


def test_scale_is_ordered() -> None:
    assert MATURITY_LEVELS == ("all", "7+", "13+", "16+", "18+")


@pytest.mark.parametrize(
    ("limit", "rating", "expected"),
    [
        ("18+", "18+", True),
        ("18+", "all", True),
        ("13+", "13+", True),
        ("13+", "16+", False),
        ("all", "7+", False),
        ("all", "all", True),
    ],
)
def test_allows(limit: str, rating: str, expected: bool) -> None:
    assert allows(limit, rating) is expected


@pytest.mark.parametrize(
    ("limit", "rating"), [("13+", "R"), ("13+", ""), ("bogus", "all"), ("", "")]
)
def test_unknown_values_fail_closed(limit: str, rating: str) -> None:
    assert allows(limit, rating) is False

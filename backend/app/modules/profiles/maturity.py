"""Maturity scale shared by profiles and (later) the catalog. See ADR-0012."""

MATURITY_LEVELS: tuple[str, ...] = ("all", "7+", "13+", "16+", "18+")
_RANK = {level: i for i, level in enumerate(MATURITY_LEVELS)}


def allows(profile_limit: str, title_rating: str) -> bool:
    """True if a profile with this limit may see a title with this rating.

    Fails closed: an unknown limit or an unknown/missing rating is never allowed.
    """
    limit, rating = _RANK.get(profile_limit), _RANK.get(title_rating)
    return limit is not None and rating is not None and rating <= limit


def allowed_ratings(profile_limit: str) -> tuple[str, ...]:
    """Ratings a profile may see, for SQL IN filters. Unknown limit -> nothing (fail closed)."""
    limit = _RANK.get(profile_limit)
    return () if limit is None else MATURITY_LEVELS[: limit + 1]

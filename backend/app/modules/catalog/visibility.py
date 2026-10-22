"""The single definition of "this title may be shown". Every catalog query must use it."""

from datetime import datetime

from sqlalchemy import ColumnElement, and_, or_

from app.modules.catalog.models import Title
from app.modules.profiles.maturity import allowed_ratings


def visible_title(now: datetime, maturity_limit: str) -> ColumnElement[bool]:
    """Published, inside its availability window, and within the maturity limit."""
    return and_(
        Title.status == "published",
        or_(Title.publish_at.is_(None), Title.publish_at <= now),
        or_(Title.available_until.is_(None), Title.available_until > now),
        Title.maturity_rating.in_(allowed_ratings(maturity_limit)),
    )

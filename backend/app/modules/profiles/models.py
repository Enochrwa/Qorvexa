import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            "maturity_limit IN ('all','7+','13+','16+','18+')", name="ck_profiles_maturity"
        ),
        Index("uq_profiles_user_name", "user_id", text("lower(name)"), unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    avatar: Mapped[str] = mapped_column(String(16), nullable=False, server_default="avatar-1")
    language: Mapped[str] = mapped_column(String(8), nullable=False, server_default="en")
    maturity_limit: Mapped[str] = mapped_column(String(8), nullable=False, server_default="13+")
    autoplay_next: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    data_saver: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    subtitle_prefs: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

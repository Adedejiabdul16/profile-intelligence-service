import secrets
import time
import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def generate_uuid7() -> str:
    """Generate a UUID version 7."""

    timestamp_ms = int(time.time() * 1000)

    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)

    value = (timestamp_ms & ((1 << 48) - 1)) << 80
    value |= 0x7 << 76
    value |= random_a << 64
    value |= 0b10 << 62
    value |= random_b

    return str(uuid.UUID(int=value))


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid7,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    gender_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    sample_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    age_group: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    country_id: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        index=True,
    )

    country_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    country_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


Index(
    "ix_profiles_gender_probability",
    Profile.gender_probability,
)

Index(
    "ix_profiles_country_probability",
    Profile.country_probability,
)
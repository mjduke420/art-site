"""Album: a named collection of photos (the Flickr-style 'set')."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .photo import Photo


class Album(Base):
    __tablename__ = "albums"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    cover_photo_id: Mapped[int | None] = mapped_column(
        ForeignKey("photos.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    photos: Mapped[list["Photo"]] = relationship(
        back_populates="album",
        cascade="all, delete-orphan",
        foreign_keys="Photo.album_id",
        order_by="Photo.sort_order, Photo.id",
    )
    cover_photo: Mapped["Photo | None"] = relationship(
        foreign_keys=[cover_photo_id], post_update=True
    )

    @property
    def photo_count(self) -> int:
        return len(self.photos)

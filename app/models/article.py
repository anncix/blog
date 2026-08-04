"""文章模型。标签以 JSON 数组存储于 article.tags，避免额外关联表。"""
import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Article(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(String(500), default="")

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # 标签：JSON 字符串数组，如 ["python", "fastapi"]
    _tags: Mapped[str] = mapped_column("tags", Text, default="[]")

    status: Mapped[str] = mapped_column(String(16), default="published")  # draft/published
    views: Mapped[int] = mapped_column(Integer, default=0)

    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def tags(self) -> list[str]:
        try:
            data = json.loads(self._tags or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(list(value or []), ensure_ascii=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Article {self.title}>"
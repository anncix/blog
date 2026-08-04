"""评论模型。支持嵌套（parent_id 自引用）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    author_name: Mapped[str] = mapped_column(String(64))
    author_email: Mapped[str] = mapped_column(String(128), default="")
    content: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/approved/rejected

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Comment {self.author_name}>"
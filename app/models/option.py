"""站点配置项模型（键值对）。用于主题、站点设置、友链等。"""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Option(Base, TimestampMixin):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    option_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    option_value: Mapped[str] = mapped_column(Text, default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Option {self.option_key}>"
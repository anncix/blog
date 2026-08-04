"""数据库引擎 / 会话 / 声明式基类。"""
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    pass


class TimestampMixin:
    """记录创建 / 更新时间。"""

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖：提供数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
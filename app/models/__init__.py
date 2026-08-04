"""ORM 模型包：统一导入并负责建表。"""
from app.models.article import Article
from app.models.base import Base, engine
from app.models.category import Category
from app.models.comment import Comment
from app.models.option import Option
from app.models.tag import Tag
from app.models.user import User

__all__ = [
    "Base",
    "engine",
    "User",
    "Article",
    "Category",
    "Tag",
    "Comment",
    "Option",
]


def create_all() -> None:
    """创建所有表（幂等）。"""
    Base.metadata.create_all(bind=engine)
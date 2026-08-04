"""Pydantic 校验模型。"""
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 用户
# ---------------------------------------------------------------------------
class UserOut(ORMModel):
    id: int
    username: str
    email: str = ""
    nickname: str = ""


class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=4, max_length=128)


# ---------------------------------------------------------------------------
# 分类 / 标签
# ---------------------------------------------------------------------------
class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=255)


class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)


# ---------------------------------------------------------------------------
# 文章
# ---------------------------------------------------------------------------
class ArticleIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    content: str = Field(default="")
    summary: str = Field(default="", max_length=500)
    category_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    status: str = Field(default="published", pattern="^(draft|published)$")


class ArticleOut(ORMModel):
    id: int
    title: str
    slug: str
    summary: str
    status: str
    views: int
    created_at: object | None = None
    updated_at: object | None = None


# ---------------------------------------------------------------------------
# 评论
# ---------------------------------------------------------------------------
class CommentIn(BaseModel):
    article_id: int
    parent_id: int | None = None
    author_name: str = Field(min_length=1, max_length=64)
    author_email: str = Field(default="", max_length=128)
    content: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# 站点配置
# ---------------------------------------------------------------------------
class OptionIn(BaseModel):
    option_key: str = Field(min_length=1, max_length=128)
    option_value: str = Field(default="")


class FriendLink(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=1, max_length=255)
    desc: str = Field(default="", max_length=255)
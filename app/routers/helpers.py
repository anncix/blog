"""模板渲染辅助：统一注入公共上下文与侧边栏数据。"""
import json
import time

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_options_dict
from app.models import Article, Category, Page, Tag
from app.utils.i18n import normalize_lang, t as _t

templates = Jinja2Templates(directory="app/templates")

# 侧边栏 TTL 缓存（秒）：避免每个请求都全量扫描文章
_SIDEBAR_TTL = 60
_SIDEBAR_CACHE: dict = {"t": 0.0, "data": None}


def resolve_lang(request: Request, options: dict) -> str:
    """语言优先级：cookie > 站点配置 > 默认 zh。"""
    cookie = request.cookies.get("lang")
    if cookie:
        return normalize_lang(cookie)
    return normalize_lang(options.get("lang"))


def _sidebar_data(db: Session) -> dict:
    """侧边栏公共数据：最新文章、热门文章、分类、标签云、友链。

    带 TTL 缓存：侧边栏只在窗口内首查时访问数据库，避免每个请求都全量扫描。
    """
    now = time.time()
    if _SIDEBAR_CACHE["data"] is not None and now - _SIDEBAR_CACHE["t"] < _SIDEBAR_TTL:
        return _SIDEBAR_CACHE["data"]

    latest = (
        db.query(Article)
        .filter(Article.status == "published")
        .order_by(Article.published_at.desc())
        .limit(5)
        .all()
    )
    hot = (
        db.query(Article)
        .filter(Article.status == "published")
        .order_by(Article.views.desc())
        .limit(5)
        .all()
    )
    categories = (
        db.query(Category, func.count(Article.id).label("cnt"))
        .outerjoin(Article, Article.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.name.asc())
        .all()
    )
    # 标签云：仅在缓存失效时统计一次标签频次
    tag_counts: dict[str, int] = {}
    for a in db.query(Article).with_entities(Article._tags).filter(Article.status == "published").all():
        try:
            for t in json.loads(a._tags or "[]"):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        except (ValueError, TypeError):
            continue
    tag_rows = (
        db.query(Tag).filter(Tag.name.in_(tag_counts.keys())).order_by(Tag.name.asc()).all()
    )
    tags = [
        (t, tag_counts.get(t.name, 0))
        for t in tag_rows
        if tag_counts.get(t.name, 0) > 0
    ]
    pages = (
        db.query(Page)
        .filter(Page.status == "published")
        .order_by(Page.published_at.asc())
        .all()
    )
    data = {
        "latest_articles": latest,
        "hot_articles": hot,
        "categories": categories,
        "tags": tags,
        "pages": pages,
    }
    _SIDEBAR_CACHE["t"] = now
    _SIDEBAR_CACHE["data"] = data
    return data


def render(
    request: Request,
    template: str,
    db: Session,
    context: dict | None = None,
    status_code: int = 200,
) -> "Response":
    """渲染模板：注入 request、站点配置与侧边栏数据。"""
    cats = db.query(Category).all()
    category_map = {c.id: c.name for c in cats}
    category_slug_map = {c.id: c.slug for c in cats}
    options = get_options_dict(db)
    lang = resolve_lang(request, options)
    ctx = {
        "request": request,
        "options": options,
        "lang": lang,
        "t": lambda key, **kw: _t(lang, key, **kw),
        "category_map": category_map,
        "category_slug_map": category_slug_map,
        **_sidebar_data(db),
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, template, ctx, status_code=status_code)
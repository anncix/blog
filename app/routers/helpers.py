"""模板渲染辅助：统一注入公共上下文与侧边栏数据。"""
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_options_dict
from app.models import Article, Category, Page, Tag
from app.utils.i18n import normalize_lang, t as _t

templates = Jinja2Templates(directory="app/templates")


def resolve_lang(request: Request, options: dict) -> str:
    """语言优先级：cookie > 站点配置 > 默认 zh。"""
    cookie = request.cookies.get("lang")
    if cookie:
        return normalize_lang(cookie)
    return normalize_lang(options.get("lang"))


def _sidebar_data(db: Session) -> dict:
    """侧边栏公共数据：最新文章、热门文章、分类、标签云、友链。"""
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
    # 标签云：从所有已发布文章统计标签频次
    tag_counts: dict[str, int] = {}
    for a in db.query(Article).filter(Article.status == "published").all():
        for t in a.tags:
            tag_counts[t] = tag_counts.get(t, 0) + 1
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
    return {
        "latest_articles": latest,
        "hot_articles": hot,
        "categories": categories,
        "tags": tags,
        "pages": pages,
    }


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
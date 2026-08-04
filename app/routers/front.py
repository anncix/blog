"""前台路由：首页、文章详情、分类/标签、归档、时间轴、友链、独立页面、搜索、评论、订阅。"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_option, get_options_dict
from app.models import Article, Category, Comment, Page, Tag
from app.models.base import get_db
from app.routers.helpers import render
from app.utils.anti_spam import check as anti_spam_check
from app.utils.feed import feed_response
from app.utils.i18n import normalize_lang
from app.utils.markdown import render_markdown
from app.utils.search import search_articles

router = APIRouter()


def _published():
    return Article.status == "published"


# ---------------------------------------------------------------------------
# 首页
# ---------------------------------------------------------------------------
@router.get("/")
def home(request: Request, page: int = 1, db: Session = Depends(get_db)):
    page = max(page, 1)
    total = db.query(Article).filter(_published()).count()
    articles = (
        db.query(Article)
        .filter(_published())
        .order_by(Article.published_at.desc())
        .offset((page - 1) * settings.PAGE_SIZE)
        .limit(settings.PAGE_SIZE)
        .all()
    )
    total_pages = max(1, (total + settings.PAGE_SIZE - 1) // settings.PAGE_SIZE)
    return render(
        request,
        "pages/index.html",
        db,
        {"articles": articles, "page": page, "total_pages": total_pages},
    )


# ---------------------------------------------------------------------------
# 文章详情
# ---------------------------------------------------------------------------
@router.get("/article/{slug}")
def article_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article or article.status != "published":
        return render(request, "pages/404.html", db, {}, status_code=404)
    article.views += 1
    db.commit()

    html = render_markdown(article.content)
    comments = (
        db.query(Comment)
        .filter(Comment.article_id == article.id, Comment.status == "approved")
        .order_by(Comment.created_at.asc())
        .all()
    )
    # 构建嵌套评论树
    tree = {}
    for c in comments:
        tree.setdefault(c.parent_id, []).append(c)
    comment_enabled = get_option(db, "comment_enabled", "1") == "1"

    return render(
        request,
        "pages/article.html",
        db,
        {
            "article": article,
            "content_html": html,
            "comment_tree": tree,
            "comments": comments,
            "comment_enabled": comment_enabled,
        },
    )


# ---------------------------------------------------------------------------
# 分类 / 标签
# ---------------------------------------------------------------------------
@router.get("/category/{slug}")
def category_view(slug: str, request: Request, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        return render(request, "pages/404.html", db, {}, status_code=404)
    articles = (
        db.query(Article)
        .filter(_published(), Article.category_id == category.id)
        .order_by(Article.published_at.desc())
        .all()
    )
    return render(
        request,
        "pages/category.html",
        db,
        {"category": category, "articles": articles},
    )


@router.get("/tag/{slug}")
def tag_view(slug: str, request: Request, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        return render(request, "pages/404.html", db, {}, status_code=404)
    articles = [
        a
        for a in db.query(Article)
        .filter(_published())
        .order_by(Article.published_at.desc())
        .all()
        if tag.name in a.tags
    ]
    return render(
        request, "pages/tag.html", db, {"tag": tag, "articles": articles}
    )


# ---------------------------------------------------------------------------
# 归档（按年月分组）
# ---------------------------------------------------------------------------
@router.get("/archive")
def archive(request: Request, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .filter(_published())
        .order_by(Article.published_at.desc())
        .all()
    )
    groups: dict[str, list] = {}
    for a in articles:
        key = a.published_at.strftime("%Y年%m月") if a.published_at else "未归档"
        groups.setdefault(key, []).append(a)
    return render(request, "pages/archive.html", db, {"groups": groups})


# ---------------------------------------------------------------------------
# 时间轴
# ---------------------------------------------------------------------------
@router.get("/timeline")
def timeline(request: Request, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .filter(_published())
        .order_by(Article.published_at.desc())
        .all()
    )
    timeline_data = []
    for a in articles:
        if a.published_at:
            timeline_data.append(
                {"date": a.published_at.strftime("%Y-%m-%d"), "article": a}
            )
    return render(request, "pages/timeline.html", db, {"timeline": timeline_data})


# ---------------------------------------------------------------------------
# 友链
# ---------------------------------------------------------------------------
@router.get("/links")
def links(request: Request, db: Session = Depends(get_db)):
    options = get_options_dict(db)
    friend_links = options.get("friend_links", [])
    return render(request, "pages/links.html", db, {"friend_links": friend_links})


# ---------------------------------------------------------------------------
# 搜索
# ---------------------------------------------------------------------------
@router.get("/search")
def search(request: Request, q: str = "", db: Session = Depends(get_db)):
    q = q.strip()
    articles = search_articles(db, q) if q else []
    return render(
        request, "pages/search.html", db, {"articles": articles, "q": q}
    )


# ---------------------------------------------------------------------------
# 评论提交
# ---------------------------------------------------------------------------
@router.post("/comment")
def submit_comment(
    request: Request,
    article_id: int = Form(...),
    author_name: str = Form(...),
    author_email: str = Form(""),
    content: str = Form(...),
    parent_id: int | None = Form(None),
    website: str = Form(""),  # 蜜罐字段
    db: Session = Depends(get_db),
):
    article = db.get(Article, article_id)
    redirect = request.headers.get("Referer")
    if not redirect or not redirect.startswith("/"):
        redirect = f"/article/{article.slug}" if article else "/"
    if not article or article.status != "published":
        return RedirectResponse(redirect, status_code=302)

    # 反垃圾：蜜罐 / 长度 / 关键词 / 频率，命中即静默成功返回
    if anti_spam_check(request, website, content):
        return RedirectResponse(redirect, status_code=302)

    comment = Comment(
        article_id=article_id,
        parent_id=parent_id,
        author_name=author_name.strip(),
        author_email=author_email.strip(),
        content=content.strip(),
        status="approved",  # 简化：默认直接通过
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    # 触发评论通知（Bark / 邮件）
    from app.utils.hooks import hooks

    hooks.trigger(
        "comment_created",
        {
            "db": db,
            "comment": comment,
            "article": article,
            "is_admin": bool(request.session.get("user_id")),
        },
    )
    return RedirectResponse(redirect, status_code=302)


# ---------------------------------------------------------------------------
# 独立页面（自定义页面）
# ---------------------------------------------------------------------------
@router.get("/page/{slug}")
def page_view(slug: str, request: Request, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page or page.status != "published":
        return render(request, "pages/404.html", db, {}, status_code=404)
    return render(
        request,
        "pages/page.html",
        db,
        {"page": page, "content_html": render_markdown(page.content)},
    )


# ---------------------------------------------------------------------------
# 语言切换
# ---------------------------------------------------------------------------
@router.get("/lang/{code}")
def switch_lang(code: str, request: Request):
    lang = normalize_lang(code)
    response = RedirectResponse(request.headers.get("Referer", "/"), status_code=302)
    response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response


# ---------------------------------------------------------------------------
# RSS / Atom 订阅
# ---------------------------------------------------------------------------
def _feed_articles(db: Session, limit: int = 20) -> list:
    return (
        db.query(Article)
        .filter(_published())
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/feed.xml")
def rss_feed(db: Session = Depends(get_db)):
    options = get_options_dict(db)
    base_url = (options.get("site_url") or settings.SITE_URL).rstrip("/")
    return feed_response("rss", base_url, options, _feed_articles(db))


@router.get("/feed.atom")
def atom_feed(db: Session = Depends(get_db)):
    options = get_options_dict(db)
    base_url = (options.get("site_url") or settings.SITE_URL).rstrip("/")
    return feed_response("atom", base_url, options, _feed_articles(db))
"""后台管理路由：Session-Cookie 认证 + 文章/评论/设置/分类/标签/友链管理。"""
import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_options_dict, set_option
from app.core.security import hash_password, verify_password
from app.models import Article, Category, Comment, Page, Tag, User
from app.models.base import get_db
from app.routers.helpers import resolve_lang, templates
from app.utils.i18n import t as _t
from app.utils.markdown import extract_summary

router = APIRouter(prefix="/admin")


def _is_admin(request: Request) -> bool:
    return bool(request.session.get("user_id"))


def _render_admin(request: Request, template: str, context: dict | None = None):
    db = request.state.db
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
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, template, ctx)


async def _require_admin(request: Request):
    if not _is_admin(request):
        raise HTTPException(
            status_code=302,
            headers={"Location": "/admin/login"},
        )
    return True


# ---------------------------------------------------------------------------
# 登录
# ---------------------------------------------------------------------------
@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if _is_admin(request):
        return RedirectResponse("/admin", status_code=302)
    request.state.db = db
    return _render_admin(request, "pages/admin/login.html")


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    from app.utils.anti_spam import _client_ip, login_limited, login_success

    ip = _client_ip(request)
    # 登录限流：同一 IP 连续失败过多则锁定
    if login_limited(ip):
        request.state.db = db
        return _render_admin(
            request,
            "pages/admin/login.html",
            {"error": "尝试过于频繁，请稍后再试"},
        )
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        request.state.db = db
        return _render_admin(
            request, "pages/admin/login.html", {"error": "用户名或密码错误"}
        )
    login_success(ip)
    request.session["user_id"] = user.id
    return RedirectResponse("/admin", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)


# ---------------------------------------------------------------------------
# 仪表盘
# ---------------------------------------------------------------------------
@router.get("")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    stats = {
        "articles": db.query(Article).count(),
        "published": db.query(Article).filter(Article.status == "published").count(),
        "drafts": db.query(Article).filter(Article.status == "draft").count(),
        "comments": db.query(Comment).count(),
        "pending_comments": db.query(Comment).filter(Comment.status == "pending").count(),
        "categories": db.query(Category).count(),
        "tags": db.query(Tag).count(),
        "views": db.query(func.sum(Article.views)).scalar() or 0,
    }
    recent = (
        db.query(Article).order_by(Article.created_at.desc()).limit(5).all()
    )
    return _render_admin(
        request, "pages/admin/dashboard.html", {"stats": stats, "recent": recent}
    )


# ---------------------------------------------------------------------------
# 文章管理
# ---------------------------------------------------------------------------
@router.get("/articles")
async def article_list(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    articles = db.query(Article).order_by(Article.created_at.desc()).all()
    return _render_admin(
        request, "pages/admin/articles.html", {"articles": articles}
    )


def _unique_slug(
    db: Session, base: str, exclude_id: int | None = None, model=Article
) -> str:
    """生成数据库中唯一的 slug，冲突时追加数字后缀。"""
    candidate = base
    n = 2
    while True:
        q = db.query(model).filter(model.slug == candidate)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        if q.first() is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1


@router.get("/articles/new")
async def article_new(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    return _render_admin(
        request,
        "pages/admin/article_edit.html",
        {"article": None, "categories": db.query(Category).all()},
    )


@router.get("/articles/{article_id}/edit")
async def article_edit(
    article_id: int, request: Request, db: Session = Depends(get_db)
):
    await _require_admin(request)
    request.state.db = db
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404)
    return _render_admin(
        request,
        "pages/admin/article_edit.html",
        {"article": article, "categories": db.query(Category).all()},
    )


@router.post("/articles/save")
async def article_save(
    request: Request,
    id: int | None = Form(None),
    title: str = Form(...),
    slug: str = Form(...),
    content: str = Form(""),
    summary: str = Form(""),
    category_id: int | None = Form(None),
    tags: str = Form(""),
    status: str = Form("published"),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db

    tag_names = [t.strip() for t in tags.split(",") if t.strip()]
    # 同步标签表
    for name in tag_names:
        if not db.query(Tag).filter(Tag.name == name).first():
            db.add(Tag(name=name, slug=name.lower().replace(" ", "-")))

    if id:
        article = db.get(Article, id)
        if not article:
            raise HTTPException(status_code=404)
    else:
        article = Article()

    article.title = title.strip()
    base_slug = slug.strip() or title.strip().lower().replace(" ", "-")
    article.slug = _unique_slug(db, base_slug, exclude_id=id)
    article.content = content
    article.summary = summary.strip() or extract_summary(content)
    article.category_id = category_id
    article.tags = tag_names
    article.status = status
    if status == "published" and not article.published_at:
        from datetime import datetime

        article.published_at = datetime.utcnow()
    db.add(article)
    db.commit()
    return RedirectResponse("/admin/articles", status_code=302)


@router.post("/articles/{article_id}/delete")
async def article_delete(
    article_id: int, request: Request, db: Session = Depends(get_db)
):
    await _require_admin(request)
    request.state.db = db
    article = db.get(Article, article_id)
    if article:
        db.delete(article)
        db.commit()
    return RedirectResponse("/admin/articles", status_code=302)


# ---------------------------------------------------------------------------
# 独立页面管理
# ---------------------------------------------------------------------------
@router.get("/pages")
async def page_list(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    pages = db.query(Page).order_by(Page.created_at.desc()).all()
    return _render_admin(request, "pages/admin/pages.html", {"pages": pages})


@router.get("/pages/new")
async def page_new(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    return _render_admin(request, "pages/admin/page_edit.html", {"page": None})


@router.get("/pages/{page_id}/edit")
async def page_edit(page_id: int, request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    page = db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404)
    return _render_admin(request, "pages/admin/page_edit.html", {"page": page})


@router.post("/pages/save")
async def page_save(
    request: Request,
    id: int | None = Form(None),
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    status: str = Form("published"),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db
    if id:
        page = db.get(Page, id)
        if not page:
            raise HTTPException(status_code=404)
    else:
        page = Page()
    page.title = title.strip()
    base_slug = slug.strip() or title.strip().lower().replace(" ", "-")
    page.slug = _unique_slug(db, base_slug, exclude_id=id, model=Page)
    page.content = content
    page.status = status
    if status == "published" and not page.published_at:
        from datetime import datetime

        page.published_at = datetime.utcnow()
    db.add(page)
    db.commit()
    return RedirectResponse("/admin/pages", status_code=302)


@router.post("/pages/{page_id}/delete")
async def page_delete(page_id: int, request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    page = db.get(Page, page_id)
    if page:
        db.delete(page)
        db.commit()
    return RedirectResponse("/admin/pages", status_code=302)


# ---------------------------------------------------------------------------
# 评论审核
# ---------------------------------------------------------------------------
@router.get("/comments")
async def comment_list(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    comments = db.query(Comment).order_by(Comment.created_at.desc()).all()
    article_ids = {c.article_id for c in comments}
    article_map = {
        a.id: a.title
        for a in db.query(Article).filter(Article.id.in_(article_ids)).all()
    }
    return _render_admin(
        request,
        "pages/admin/comments.html",
        {"comments": comments, "article_map": article_map},
    )


@router.post("/comments/{comment_id}/status")
async def comment_status(
    comment_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db
    comment = db.get(Comment, comment_id)
    if comment and status in ("approved", "pending", "rejected"):
        comment.status = status
        db.commit()
    return RedirectResponse("/admin/comments", status_code=302)


@router.post("/comments/{comment_id}/delete")
async def comment_delete(
    comment_id: int, request: Request, db: Session = Depends(get_db)
):
    await _require_admin(request)
    request.state.db = db
    comment = db.get(Comment, comment_id)
    if comment:
        db.delete(comment)
        db.commit()
    return RedirectResponse("/admin/comments", status_code=302)


# ---------------------------------------------------------------------------
# 站点设置
# ---------------------------------------------------------------------------
@router.get("/settings")
async def settings_page(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    options = get_options_dict(db)
    categories = db.query(Category).order_by(Category.name.asc()).all()
    category_counts = dict(
        db.query(Article.category_id, func.count(Article.id))
        .filter(Article.category_id.isnot(None))
        .group_by(Article.category_id)
        .all()
    )
    return _render_admin(
        request,
        "pages/admin/settings.html",
        {"options": options, "categories": categories, "category_counts": category_counts},
    )


@router.post("/settings")
async def settings_save(
    request: Request,
    site_name: str = Form(""),
    site_desc: str = Form(""),
    site_keywords: str = Form(""),
    site_author: str = Form(""),
    site_avatar: str = Form(""),
    site_bio: str = Form(""),
    footer_text: str = Form(""),
    theme_color: str = Form("indigo"),
    dark_mode: str = Form("system"),
    comment_enabled: str = Form("1"),
    ga_code: str = Form(""),
    site_url: str = Form(""),
    lang: str = Form("zh"),
    bark_enabled: str = Form("0"),
    bark_key: str = Form(""),
    bark_server: str = Form("https://api.day.app"),
    email_enabled: str = Form("0"),
    smtp_host: str = Form(""),
    smtp_port: str = Form("465"),
    smtp_user: str = Form(""),
    smtp_password: str = Form(""),
    smtp_from: str = Form(""),
    smtp_use_tls: str = Form("1"),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db
    data = {
        "site_name": site_name,
        "site_desc": site_desc,
        "site_keywords": site_keywords,
        "site_author": site_author,
        "site_avatar": site_avatar,
        "site_bio": site_bio,
        "footer_text": footer_text,
        "theme_color": theme_color,
        "dark_mode": dark_mode,
        "comment_enabled": comment_enabled,
        "ga_code": ga_code,
        "site_url": site_url,
        "lang": lang,
        # 通知配置
        "bark_enabled": bark_enabled,
        "bark_key": bark_key,
        "bark_server": bark_server,
        "email_enabled": email_enabled,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
        "smtp_from": smtp_from,
        "smtp_use_tls": smtp_use_tls,
    }
    for k, v in data.items():
        set_option(db, k, v)
    return RedirectResponse("/admin/settings", status_code=302)


# ---------------------------------------------------------------------------
# 友链管理
# ---------------------------------------------------------------------------
def _load_links(db: Session) -> list[dict]:
    value = get_options_dict(db).get("friend_links", [])
    return value if isinstance(value, list) else []


@router.get("/links")
async def links_page(request: Request, db: Session = Depends(get_db)):
    await _require_admin(request)
    request.state.db = db
    return _render_admin(
        request, "pages/admin/links.html", {"links": _load_links(db)}
    )


@router.post("/links")
async def links_save(
    request: Request,
    links_json: str = Form("[]"),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db
    try:
        links = json.loads(links_json)
        if not isinstance(links, list):
            raise ValueError
    except (ValueError, TypeError):
        links = []
    set_option(db, "friend_links", json.dumps(links, ensure_ascii=False))
    return RedirectResponse("/admin/links", status_code=302)


# ---------------------------------------------------------------------------
# 分类管理
# ---------------------------------------------------------------------------
@router.post("/categories/add")
async def category_add(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    await _require_admin(request)
    request.state.db = db
    if db.query(Category).filter(Category.name == name).first() is None:
        db.add(Category(name=name.strip(), slug=slug.strip() or name.strip(), description=description))
        db.commit()
    return RedirectResponse("/admin/settings", status_code=302)


@router.post("/categories/{category_id}/delete")
async def category_delete(
    category_id: int, request: Request, db: Session = Depends(get_db)
):
    await _require_admin(request)
    request.state.db = db
    category = db.get(Category, category_id)
    if category:
        db.delete(category)
        db.commit()
    return RedirectResponse("/admin/settings", status_code=302)
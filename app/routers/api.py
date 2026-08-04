"""API 路由：前后端分离的 JSON 接口（JWT 认证）。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_admin
from app.core.security import create_access_token
from app.models import Article, Category, Comment, Tag
from app.models.base import get_db
from app.schemas import ArticleIn, ArticleOut, CommentIn, LoginIn, UserOut
from app.utils.markdown import render_markdown

router = APIRouter(prefix="/api")


@router.post("/auth/login", response_model=dict)
def api_login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    from app.models import User

    from app.core.security import verify_password
    from app.utils.anti_spam import _client_ip, login_limited, login_success

    if login_limited(_client_ip(request)):
        raise HTTPException(status_code=429, detail="尝试过于频繁，请稍后再试")
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    login_success(_client_ip(request))
    token = create_access_token(user.id, {"username": user.username})
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user).model_dump()}


@router.get("/articles", response_model=list[ArticleOut])
def api_articles(
    page: int = Query(1, ge=1),
    category: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Article).filter(Article.status == "published")
    if category:
        cat = db.query(Category).filter(Category.slug == category).first()
        if cat:
            query = query.filter(Article.category_id == cat.id)
    if tag:
        query = query.filter(Article._tags.like(f"%{tag}%"))
    articles = (
        query.order_by(Article.published_at.desc())
        .offset((page - 1) * settings.PAGE_SIZE)
        .limit(settings.PAGE_SIZE)
        .all()
    )
    return [ArticleOut.model_validate(a) for a in articles]


@router.get("/articles/{slug}", response_model=dict)
def api_article(slug: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article or article.status != "published":
        raise HTTPException(status_code=404, detail="文章不存在")
    return {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "summary": article.summary,
        "tags": article.tags,
        "views": article.views,
        "content_html": render_markdown(article.content),
        "created_at": article.created_at.isoformat() if article.created_at else None,
    }


@router.post("/comments", response_model=dict)
def api_comment(data: CommentIn, request: Request, db: Session = Depends(get_db)):
    article = db.get(Article, data.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    # 反垃圾：关键词 / 频率 / 长度
    from app.utils.anti_spam import check as anti_spam_check

    if anti_spam_check(request, "", data.content):
        raise HTTPException(status_code=400, detail="评论未通过反垃圾检查")
    comment = Comment(
        article_id=data.article_id,
        parent_id=data.parent_id,
        author_name=data.author_name,
        author_email=data.author_email,
        content=data.content,
        status="approved",
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    # 触发评论通知（Bark / 邮件）
    from app.utils.hooks import hooks

    from app.core.deps import get_options_dict

    base_url = (get_options_dict(db).get("site_url") or settings.SITE_URL).rstrip("/")
    hooks.trigger(
        "comment_created",
        {
            "db": db,
            "comment": comment,
            "article": article,
            "is_admin": False,
            "base_url": base_url,
        },
    )
    return {"ok": True, "id": comment.id}


@router.get("/archive", response_model=list[dict])
def api_archive(db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .filter(Article.status == "published")
        .order_by(Article.published_at.desc())
        .all()
    )
    groups: dict[str, list] = {}
    for a in articles:
        key = a.published_at.strftime("%Y-%m") if a.published_at else "unknown"
        groups.setdefault(key, []).append(a.title)
    return [{"month": k, "titles": v} for k, v in groups.items()]


@router.get("/search", response_model=list[dict])
def api_search(q: str = Query("", min_length=1), db: Session = Depends(get_db)):
    like = f"%{q}%"
    articles = (
        db.query(Article)
        .filter(Article.status == "published", or_(Article.title.like(like), Article.content.like(like)))
        .order_by(Article.published_at.desc())
        .limit(20)
        .all()
    )
    return [{"id": a.id, "title": a.title, "slug": a.slug} for a in articles]


# 受保护示例：需要 JWT
@router.get("/admin/ping", response_model=dict)
def admin_ping(user=Depends(require_admin)):
    return {"ok": True, "user": user.username}
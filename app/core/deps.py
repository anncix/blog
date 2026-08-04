"""依赖注入：会话、当前用户、站点配置、模板上下文。"""
import json

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.models import Option, User
from app.models.base import get_db

# 可在模板中直接访问的全局配置键
PUBLIC_KEYS = [
    "site_name",
    "site_desc",
    "site_keywords",
    "site_author",
    "site_avatar",
    "site_bio",
    "footer_text",
    "theme_color",
    "dark_mode",
    "friend_links",
    "comment_enabled",
    "ga_code",
    "site_url",
    "lang",
    # 通知配置
    "bark_enabled",
    "bark_key",
    "bark_server",
    "email_enabled",
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "smtp_from",
    "smtp_use_tls",
]


# ---------------------------------------------------------------------------
# 站点配置读写
# ---------------------------------------------------------------------------
def get_option(db: Session, key: str, default: str = "") -> str:
    """读取单个配置项。"""
    row = db.query(Option).filter(Option.option_key == key).first()
    return row.option_value if row else default


def set_option(db: Session, key: str, value: str) -> Option:
    """写入（upsert）单个配置项。"""
    row = db.query(Option).filter(Option.option_key == key).first()
    if row:
        row.option_value = value
    else:
        row = Option(option_key=key, option_value=value)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_options_dict(db: Session, keys: list[str] | None = None) -> dict:
    """读取配置为 dict。"""
    keys = keys or PUBLIC_KEYS
    rows = db.query(Option).filter(Option.option_key.in_(keys)).all()
    data = {r.option_key: r.option_value for r in rows}
    # 补默认值
    defaults = {
        "site_name": settings.APP_NAME,
        "site_desc": "一个简洁优雅的博客",
        "site_author": "Admin",
        "theme_color": "indigo",
        "dark_mode": "system",
        "comment_enabled": "1",
        "friend_links": "[]",
        "site_url": settings.SITE_URL,
        "lang": "zh",
        # 通知
        "bark_enabled": "0",
        "bark_key": "",
        "bark_server": "https://api.day.app",
        "email_enabled": "0",
        "smtp_host": "",
        "smtp_port": "465",
        "smtp_user": "",
        "smtp_password": "",
        "smtp_from": "",
        "smtp_use_tls": "1",
    }
    for k, v in defaults.items():
        data.setdefault(k, v)
    # 解析友链 JSON
    try:
        data["friend_links"] = json.loads(data.get("friend_links", "[]"))
    except (ValueError, TypeError):
        data["friend_links"] = []
    return data


# ---------------------------------------------------------------------------
# 认证依赖
# ---------------------------------------------------------------------------
def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    """从 Session-Cookie 或 Authorization Bearer(JWT) 解析当前用户。"""
    user_id = request.session.get("user_id")
    if user_id:
        user = db.get(User, user_id)
        if user and user.is_active:
            return user

    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_access_token(auth[7:])
        if payload:
            user = db.get(User, payload.get("sub"))
            if user and user.is_active:
                return user
    return None


def require_admin(user: User | None = Depends(get_current_user)) -> User:
    """需要登录的管理员依赖。"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    return user


# ---------------------------------------------------------------------------
# 模板上下文
# ---------------------------------------------------------------------------
def template_context(
    request: Request, db: Session = Depends(get_db)
) -> dict:
    """Injected into templates via APIRouter dependencies. 返回站点配置等。"""
    options = get_options_dict(db)
    return {
        "options": options,
        "request": request,
    }
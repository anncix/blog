"""通知模块：Bark 推送 + 邮件通知。

- Bark：用户评论时推送给管理员手机。
- 邮件：管理员回复评论时通知被回复的用户。

所有通知失败均静默处理，不影响主流程。
"""
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.header import Header
from email.mime.text import MIMEText

from app.core.deps import get_option
from app.models import Comment
from app.utils.hooks import hooks


def _enabled(db, key: str) -> bool:
    return get_option(db, key, "0") == "1"


# ---------------------------------------------------------------------------
# Bark 推送
# ---------------------------------------------------------------------------
def send_bark(db, title: str, body: str, url: str | None = None,
              group: str = "blog") -> bool:
    """发送 Bark 推送。失败静默返回 False。"""
    if not _enabled(db, "bark_enabled"):
        return False
    key = get_option(db, "bark_key", "").strip()
    if not key:
        return False
    server = get_option(db, "bark_server", "https://api.day.app").strip().rstrip("/")
    endpoint = (
        f"{server}/{key}/"
        f"{urllib.parse.quote(title)}/{urllib.parse.quote(body)}"
    )
    params = {"group": group}
    if url:
        params["url"] = url
    endpoint += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(endpoint, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 邮件通知
# ---------------------------------------------------------------------------
def send_email(db, to: str, subject: str, body: str) -> bool:
    """通过 SMTP 发送邮件。失败静默返回 False。"""
    if not _enabled(db, "email_enabled"):
        return False
    host = get_option(db, "smtp_host", "").strip()
    if not host or not to:
        return False
    port = int(get_option(db, "smtp_port", "465") or "465")
    user = get_option(db, "smtp_user", "").strip()
    password = get_option(db, "smtp_password", "").strip()
    sender = get_option(db, "smtp_from", user).strip() or user
    use_tls = get_option(db, "smtp_use_tls", "1") == "1"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender
    msg["To"] = to

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as server:
                if user:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                if user:
                    server.login(user, password)
                server.send_message(msg)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 钩子处理器：把通知接入 hooks 事件
# ---------------------------------------------------------------------------
def _on_comment_created(context: dict) -> dict:
    """评论 / 回复事件 → 通知。

    - 管理员回复用户评论 → 邮件通知被回复的用户。
    - 普通用户评论 → Bark 推送通知管理员。
    """
    db = context.get("db")
    comment = context.get("comment")
    article = context.get("article")
    if not db or not comment or not article:
        return context
    article_url = f"{context.get('base_url', '')}/article/{article.slug}"

    # 管理员回复 → 邮件通知被回复的用户
    if context.get("is_admin") and comment.parent_id:
        target = db.get(Comment, comment.parent_id)
        if target and target.author_email:
            subject = f"你在「{article.title}」收到了新的回复"
            body = (
                f"你好，{target.author_name}：\n\n"
                f"{comment.author_name} 回复了你的评论：\n"
                f"「{comment.content}」\n\n"
                f"查看详情：{article_url}"
            )
            send_email(db, target.author_email, subject, body)
        return context

    # 普通用户评论 → Bark 通知管理员
    body = f"{comment.author_name}：{comment.content[:60]}"
    send_bark(db, "新评论", body, url=article_url)
    return context


def setup_notify_hooks() -> None:
    """注册通知相关钩子（在应用启动时调用）。"""
    hooks.register("comment_created", _on_comment_created)
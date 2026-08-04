"""FastAPI 应用入口。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, create_all
from app.models.base import SessionLocal, engine
from app.routers import admin, api, front

logger = logging.getLogger(__name__)


def _warn_security() -> None:
    """上线前安全提醒：默认密钥 / 默认管理员密码 / 调试模式。"""
    if settings.SECRET_KEY == "dev-secret-change-me":
        logger.warning(
            "安全提醒：SECRET_KEY 仍为默认值，session 与 JWT 可被伪造。请通过环境变量设置强随机密钥。"
        )
    if settings.DEBUG:
        logger.warning("安全提醒：DEBUG 处于开启状态，生产环境请设为 false。")
    if settings.ADMIN_PASSWORD == "admin123":
        logger.warning("安全提醒：默认管理员密码 admin123 存在风险，请尽快修改。")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _warn_security()
    create_all()
    _bootstrap_admin()
    # 依序初始化：先建表，再建 FTS 索引，最后注册钩子
    from app.utils.search import setup_fts

    setup_fts(engine)
    from app.utils.notify import setup_notify_hooks

    setup_notify_hooks()
    yield


def _bootstrap_admin() -> None:
    """首次启动时创建默认管理员。"""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == settings.ADMIN_USERNAME).first() is None:
            db.add(
                User(
                    username=settings.ADMIN_USERNAME,
                    email=settings.ADMIN_EMAIL,
                    nickname=settings.ADMIN_USERNAME,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                )
            )
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Session-Cookie（后台登录）
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="blog_session",
    max_age=60 * 60 * 24 * 7,
)

# 静态资源
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# 路由
app.include_router(front.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.exception_handler(404)
async def not_found(request: Request, exc):
    from app.routers.helpers import render
    from app.models.base import SessionLocal

    db = SessionLocal()
    try:
        return render(request, "pages/404.html", db, {}, status_code=404)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.VERSION}
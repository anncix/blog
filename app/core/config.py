"""应用核心配置。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    """应用配置，集中管理常量，可通过环境变量覆盖。"""

    APP_NAME: str = "Anncix Blog"
    VERSION: str = "0.0.3"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'blog.db'}"
    )

    # 安全
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # 默认管理员（首次启动时自动创建）
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")

    # 静态 / 模板目录
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

    # 分页
    PAGE_SIZE: int = 6

    # 站点基础 URL（用于 RSS/Atom 生成绝对链接，默认 http://localhost:8000）
    SITE_URL: str = os.getenv("SITE_URL", "http://localhost:8000").rstrip("/")


settings = Settings()
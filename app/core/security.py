"""安全相关：密码哈希与 JWT 签发/校验。"""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# 密码哈希（PBKDF2，无第三方依赖）
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """生成 PBKDF2 哈希，格式：pbkdf2$iterations$salt_hex$hash_hex。"""
    salt = os.urandom(16)
    iterations = 120_000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码。兼容不同迭代次数。"""
    try:
        scheme, iterations, salt_hex, hash_hex = password_hash.split("$")
        if scheme != "pbkdf2":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    """签发 JWT。"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """校验 JWT，失败返回 None。"""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
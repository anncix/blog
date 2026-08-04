"""评论反垃圾：蜜罐字段 + IP 频率限制 + 关键词过滤。

- 蜜罐：表单中隐藏字段，机器人会填写，人工不会 → 命中即拒绝。
- 频率限制：同一 IP 短时间内多次提交 → 拒绝。
- 关键词：命中常见垃圾词 → 拒绝（静默，不暴露规则）。

所有拦截均为静默成功返回，避免机器人得知被拦截后重试。
"""
import re
import time
from collections import defaultdict, deque

# 常见垃圾特征词（含中文/英文），命中即判定为垃圾
_SPAM_KEYWORDS = (
    "加微信", "联系我", "免费领取", "兼职", "代开发票", "贷款", "赌博", "博彩", "彩票",
    "seo", "backlink", "buy now", "free money", "casino", "gambling", "viagra",
    "xxx", "click here", "make money", "open source is dead",
)

# 简单校验：评论内容最少/最多长度
MIN_CONTENT_LEN = 2
MAX_CONTENT_LEN = 2000

# IP 频率限制：窗口秒数 / 窗口内最大次数
_RATE_WINDOW = 60
_RATE_MAX = 5

# 内存记录：ip -> (时间戳队列)
_RECORDS: dict[str, deque] = defaultdict(deque)


def _client_ip(request) -> str:
    """从请求解析客户端 IP（兼容常见反代头）。"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("X-Real-IP")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


def is_honeypot_filled(honeypot: str) -> bool:
    """蜜罐字段被填写即判定为机器人。"""
    return bool(honeypot and honeypot.strip())


def rate_limited(ip: str) -> bool:
    """对指定 IP 做频率限制，超限返回 True。"""
    now = time.time()
    q = _RECORDS[ip]
    while q and now - q[0] > _RATE_WINDOW:
        q.popleft()
    if len(q) >= _RATE_MAX:
        return True
    q.append(now)
    return False


def is_spam_keyword(text: str) -> bool:
    """命中垃圾关键词返回 True。"""
    low = text.lower()
    return any(kw in low for kw in _SPAM_KEYWORDS)


def valid_content(text: str) -> bool:
    """校验评论内容长度。"""
    return MIN_CONTENT_LEN <= len(text.strip()) <= MAX_CONTENT_LEN


def check(request, honeypot: str, content: str) -> str | None:
    """综合反垃圾检查，返回错误码；通过则返回 None。

    错误码：honeypot / rate / keyword / invalid_length
    """
    if is_honeypot_filled(honeypot):
        return "honeypot"
    if not valid_content(content):
        return "invalid_length"
    if is_spam_keyword(content):
        return "keyword"
    ip = _client_ip(request)
    if rate_limited(ip):
        return "rate"
    return None
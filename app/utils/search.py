"""全文搜索：SQLite FTS5 虚拟表 + 触发器同步。

在 `articles` 表上创建 `articles_fts` 虚拟表，通过触发器在插入/更新/删除时
自动同步，实现快速全文检索（标题 + 正文 + 摘要）。若 FTS5 不可用则回退到
LIKE 查询。
"""
import re

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.models import Article

_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title, content, summary, content='articles', content_rowid='id'
)
"""

_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
      INSERT INTO articles_fts(rowid, title, content, summary)
      VALUES (new.id, new.title, new.content, new.summary);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
      VALUES ('delete', old.id, old.title, old.content, old.summary);
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
      INSERT INTO articles_fts(articles_fts, rowid, title, content, summary)
      VALUES ('delete', old.id, old.title, old.content, old.summary);
      INSERT INTO articles_fts(rowid, title, content, summary)
      VALUES (new.id, new.title, new.content, new.summary);
    END
    """,
]


def setup_fts(engine: Engine) -> bool:
    """初始化 FTS5 虚拟表与触发器。返回是否成功。"""
    try:
        with engine.begin() as conn:
            conn.execute(text(_FTS_SQL))
            for trigger in _TRIGGERS:
                conn.execute(text(trigger))
        return True
    except Exception:
        # FTS5 不可用（如某些 SQLite 构建），回退到 LIKE 搜索
        return False


def fts_available(engine: Engine) -> bool:
    """检查 FTS5 是否可用。"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT count(*) FROM articles_fts"))
        return True
    except Exception:
        return False


def search_articles(db, query: str, limit: int = 50) -> list:
    """使用 FTS5 搜索；失败时回退到 LIKE。"""
    q = query.strip()
    if not q:
        return []
    # 转义 FTS5 查询语法
    esc = re.sub(r'(\"|\\|[*^()~])', r" ", q)
    try:
        rows = db.execute(
            text(
                "SELECT id FROM articles_fts WHERE articles_fts MATCH :q "
                "ORDER BY rank LIMIT :limit"
            ),
            {"q": esc, "limit": limit},
        ).all()
        ids = [r[0] for r in rows]
        if not ids:
            return []
        return (
            db.query(Article)
            .filter(Article.id.in_(ids), Article.status == "published")
            .order_by(Article.published_at.desc())
            .all()
        )
    except Exception:
        return _like_search(db, q, limit)


def _like_search(db, query: str, limit: int) -> list:
    """LIKE 回退搜索。"""
    from sqlalchemy import or_

    like = f"%{query}%"
    return (
        db.query(Article)
        .filter(
            Article.status == "published",
            or_(Article.title.like(like), Article.content.like(like), Article.summary.like(like)),
        )
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )
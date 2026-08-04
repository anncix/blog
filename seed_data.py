"""添加示例数据到博客数据库。"""
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/workspace")

from app.models import create_all
from app.models.base import SessionLocal
from app.models import Article, Category, Tag, Comment, Option

db = SessionLocal()
create_all()

# 检查是否已有数据
if db.query(Article).count() > 0:
    print("数据库中已有文章数据，跳过种子数据")
    db.close()
    sys.exit(0)

# 创建分类
categories = [
    Category(name="技术", slug="tech", description="技术相关文章"),
    Category(name="生活", slug="life", description="生活随笔"),
    Category(name="教程", slug="tutorial", description="编程教程"),
]
for c in categories:
    db.add(c)
db.flush()

cat_tech = categories[0].id
cat_life = categories[1].id
cat_tutorial = categories[2].id

# 创建示例文章
articles = [
    Article(
        title="欢迎使用 Anncix Blog",
        slug="welcome-to-anncix-blog",
        content="""# 欢迎使用 Anncix Blog

这是一个基于 **FastAPI** 构建的轻量级博客系统。

## 主要功能

- 📝 文章发布与管理
- 🏷️ 分类与标签
- 💬 评论系统
- 🎨 响应式设计
- 🌙 暗色模式支持
- 🔔 Bark/邮件通知

## 技术栈

- **FastAPI** - 高性能 Web 框架
- **SQLAlchemy** - ORM
- **Jinja2** - 模板引擎
- **Bootstrap 5** - 前端框架
- **Mistune** - Markdown 渲染

感谢使用，希望你喜欢！
""",
        summary="这是一个基于 FastAPI 构建的轻量级博客系统，支持文章管理、分类标签、评论系统等功能。",
        category_id=cat_tech,
        author_id=1,
        status="published",
        views=128,
        published_at=datetime.utcnow() - timedelta(days=5),
    ),
    Article(
        title="FastAPI 入门指南",
        slug="fastapi-getting-started",
        content="""# FastAPI 入门指南

FastAPI 是一个现代、高性能的 Python Web 框架。

## 安装

```bash
pip install fastapi uvicorn
```

## 第一个应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello World"}
```

运行：

```bash
uvicorn main:app --reload
```

## 自动文档

启动后访问 `/docs` 即可看到自动生成的 API 文档。
""",
        summary="FastAPI 是一个现代、高性能的 Python Web 框架，本文介绍如何快速入门。",
        category_id=cat_tutorial,
        author_id=1,
        status="published",
        views=256,
        published_at=datetime.utcnow() - timedelta(days=3),
    ),
    Article(
        title="我的编程学习之路",
        slug="my-programming-journey",
        content="""# 我的编程学习之路

## 初入编程

记得第一次接触编程是在大学时期，那时候学的是 C 语言。指针、数组、链表，每一个概念都让我既兴奋又困惑。

## 学习 Python

工作后开始接触 Python，它的简洁优雅让我着迷。人生苦短，我用 Python。

## 写博客的原因

- 记录学习过程
- 分享经验心得
- 结识志同道合的朋友

> 代码改变世界，学习永无止境。
""",
        summary="回顾自己从大学到工作的编程学习经历，分享一些感悟。",
        category_id=cat_life,
        author_id=1,
        status="published",
        views=89,
        published_at=datetime.utcnow() - timedelta(days=1),
    ),
    Article(
        title="SQLAlchemy ORM 使用技巧",
        slug="sqlalchemy-orm-tips",
        content="""# SQLAlchemy ORM 使用技巧

## 查询优化

1. 使用 `selectinload` 预加载关联数据
2. 避免 N+1 查询问题
3. 合理使用索引

## 事务管理

使用 `session.begin()` 确保原子性操作。

## 总结

ORM 让数据库操作更简单，但也要注意性能问题。
""",
        summary="分享 SQLAlchemy ORM 的常用技巧和最佳实践。",
        category_id=cat_tutorial,
        author_id=1,
        status="published",
        views=67,
        published_at=datetime.utcnow() - timedelta(hours=12),
    ),
    Article(
        title="周末随笔",
        slug="weekend-notes",
        content="""# 周末随笔

又是一个安静的周末，泡一杯咖啡，坐在电脑前写代码，感觉格外惬意。

窗外阳光正好，生活如此美好。
""",
        summary="一个普通周末的随想。",
        category_id=cat_life,
        author_id=1,
        status="published",
        views=34,
        published_at=datetime.utcnow() - timedelta(hours=6),
    ),
    Article(
        title="草稿示例",
        slug="draft-example",
        content="# 这是一篇草稿\n\n这篇文章尚未发布。",
        summary="这是一篇草稿。",
        category_id=cat_tech,
        author_id=1,
        status="draft",
        views=0,
        published_at=None,
    ),
]

# 设置标签
articles[0].tags = ["fastapi", "blog", "python"]
articles[1].tags = ["fastapi", "tutorial", "python"]
articles[2].tags = ["life", "programming"]
articles[3].tags = ["sqlalchemy", "database", "python"]
articles[4].tags = ["life"]
articles[5].tags = ["draft"]

for a in articles:
    db.add(a)
db.flush()

# 创建标签
tag_names = set()
for a in articles:
    tag_names.update(a.tags)
for name in tag_names:
    existing = db.query(Tag).filter(Tag.name == name).first()
    if not existing:
        db.add(Tag(name=name, slug=name.lower().replace(" ", "-")))

# 创建示例评论
comments = [
    Comment(
        article_id=articles[0].id,
        author_name="张三",
        author_email="zhangsan@example.com",
        content="这个博客系统看起来不错！",
        status="approved",
    ),
    Comment(
        article_id=articles[0].id,
        author_name="李四",
        author_email="lisi@example.com",
        content="FastAPI 确实很好用，速度快！",
        status="approved",
    ),
    Comment(
        article_id=articles[1].id,
        author_name="王五",
        author_email="wangwu@example.com",
        content="教程写得很清楚，学到了！",
        status="approved",
    ),
]
for c in comments:
    db.add(c)

# 设置站点选项
friend_links = [
    {"name": "FastAPI 官网", "url": "https://fastapi.tiangolo.com", "desc": "FastAPI 官方网站"},
    {"name": "Python 官网", "url": "https://python.org", "desc": "Python 编程语言"},
]
site_options = {
    "site_name": "Anncix Blog",
    "site_desc": "一个基于 FastAPI 的轻量级博客系统",
    "site_author": "Admin",
    "site_bio": "热爱编程，热爱生活",
    "footer_text": "© 2024 Anncix Blog. Built with FastAPI.",
    "theme_color": "indigo",
    "dark_mode": "system",
    "comment_enabled": "1",
    "friend_links": json.dumps(friend_links, ensure_ascii=False),
}
for key, value in site_options.items():
    db.add(Option(option_key=key, option_value=value))

db.commit()
db.close()
print("示例数据添加成功！")
print(f"- 分类: {len(categories)} 个")
print(f"- 文章: {len([a for a in articles if a.status == 'published'])} 篇已发布, 1 篇草稿")
print(f"- 标签: {len(tag_names)} 个")
print(f"- 评论: {len(comments)} 条")

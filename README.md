# Anncix Blog

> 类 Handsome 风格的轻量博客 · FastAPI + SQLite + Jinja2 服务端渲染

基于 FastAPI 构建的简洁优雅博客，采用服务端渲染（SSR）输出 HTML，静态资源本地托管，开箱即用。支持深色/浅色模式、多主题配色、毛玻璃顶栏、Pjax 无刷新、Markdown 文章、嵌套评论、归档、时间轴、友链与后台管理。

## 版本

**v0.0.1** — 首个可用版本。

## 功能特性

- **前台（前后端分离展示）**
  - 首页文章卡片流（Bootstrap 栅格两列布局）
  - 文章详情：mistune 解析 Markdown + 嵌套评论区 + 图片懒加载
  - 分类 / 标签页、文章归档（按年-月分组）、时间轴、友链页
  - 全文搜索（标题 / 内容）
  - 侧边栏：个人资料、最新文章、热门文章、分类、标签云
- **后台管理（`/admin`）**
  - Session-Cookie 单用户登录（默认 `admin / admin123`）
  - 文章编辑：textarea 写 Markdown + 实时预览
  - 评论审核（通过 / 驳回 / 删除）
  - 站点设置表单：主题色、默认模式、站点信息等，存 `options` 表
  - 友链管理、分类管理
- **技术亮点**
  - Jinja2 模板继承 + 组件拆分（components/）
  - CSS 变量驱动多配色 + 深色 / 浅色模式切换
  - 毛玻璃固定顶栏 + 双栏响应式布局
  - Pjax 无刷新加载、图片懒加载、返回顶部
  - 前后端分离演示：`/api` 提供 JSON 接口（JWT 认证）

## 技术栈

| 层 | 技术 |
| --- | --- |
| Web 框架 | FastAPI |
| 数据库 | SQLite + SQLAlchemy 2.0 |
| 模板 | Jinja2 |
| 校验 | Pydantic v2 |
| Markdown | mistune |
| 认证 | Session-Cookie（后台）+ JWT（API）|

## 目录结构

```
app/
├── core/            # 配置 / 安全(JWT·密码) / 依赖注入
├── models/          # SQLAlchemy 6 张表模型
├── schemas/         # Pydantic 校验
├── routers/         # 前台 / 后台 / API 路由分离
├── utils/           # Markdown 解析 / 钩子预留
├── templates/
│   ├── base.html               # 基础骨架
│   ├── components/             # header/nav/sidebar/footer/card/comments
│   └── pages/                  # 首页·详情·分类·标签·归档·时间轴·友链·搜索·后台
└── static/          # 静态资源（CSS/JS/本地 Bootstrap）
run.py               # 开发启动脚本
requirements.txt
```

## 数据模型（6 表）

`users` · `articles` · `categories` · `tags` · `comments`（自引用嵌套）· `options`（站点配置键值对，含友链 JSON）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务（首次自动建表并创建默认管理员）
python run.py
# 或
uvicorn app.main:app --reload --port 8000
```

访问：
- 前台：http://localhost:8000
- 后台：http://localhost:8000/admin （默认账号 `admin` / `admin123`）
- API 文档：http://localhost:8000/docs

## 环境变量（可选）

可通过 `.env` 或环境变量覆盖，详见 `app/core/config.py`：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///blog.db` | 数据库连接 |
| `SECRET_KEY` | `dev-secret-change-me` | 会话 / JWT 密钥 |
| `ADMIN_USERNAME` | `admin` | 默认管理员账号 |
| `ADMIN_PASSWORD` | `admin123` | 默认管理员密码 |
| `DEBUG` | `true` | 调试模式 |

## 后台说明

- 登录：`/admin/login`，Session-Cookie 认证（单用户，暂未做多级权限）。
- 文章：`/admin/articles` 列表、`/admin/articles/new` 新建、`/admin/articles/{id}/edit` 编辑（Markdown 实时预览）。
- 评论：`/admin/comments` 审核。
- 设置：`/admin/settings` 站点信息 / 主题 / 评论开关 / 分类管理。
- 友链：`/admin/links` 增删改，保存到 `options.friend_links`。

## API（前后端分离演示）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 登录获取 JWT |
| GET | `/api/articles` | 文章列表（分页 / 分类 / 标签过滤）|
| GET | `/api/articles/{slug}` | 文章详情（含 HTML）|
| POST | `/api/comments` | 提交评论 |
| GET | `/api/archive` | 归档 |
| GET | `/api/search` | 搜索 |
| GET | `/api/admin/ping` | 受保护接口（需 Bearer JWT）|

## 更新记录

### v0.0.1（2026-08-04）
- 搭建完整项目骨架：`app/` 分层（core / models / schemas / routers / utils）
- 实现 6 表模型与基础数据初始化
- 完成前台页面：首页、文章详情、分类、标签、归档、时间轴、友链、搜索
- 完成后台管理：登录、文章 CRUD、评论审核、站点设置、友链、分类
- 实现主题系统（CSS 变量 + 深色/浅色 + 多配色）、毛玻璃顶栏、Pjax、图片懒加载
- 集成 mistune Markdown 渲染与嵌套评论
- 提供 `/api` JSON 接口（JWT 认证）演示前后端分离

## License

[MIT](LICENSE)
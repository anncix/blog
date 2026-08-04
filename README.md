# Anncix Blog

> 类 Handsome 风格的轻量博客 · FastAPI + SQLite + Jinja2 服务端渲染

基于 FastAPI 构建的简洁优雅博客，采用服务端渲染（SSR）输出 HTML，静态资源本地托管，开箱即用。支持深色/浅色模式、多主题配色、毛玻璃顶栏、Pjax 无刷新、Markdown 文章、嵌套评论、归档、时间轴、友链、独立页面、RSS/Atom 订阅、全文搜索与后台管理。

## 版本

**v0.0.5** — 修复通知邮件链接、i18n 残留、Pjax 按钮事件、GA 统计代码未注入。

**v0.0.4** — 安全加固与性能优化：登录限流、Markdown URL 白名单、侧边栏/配置 TTL 缓存、分类/标签分页、安全默认值。

**v0.0.3** — 新增 RSS/Atom 订阅、独立页面、全文搜索、评论反垃圾、中英双语、GPLv3 开源协议。

**v0.0.2** — 新增评论通知：Bark 推送 + 邮件通知 + 后台设置。

**v0.0.1** — 首个可用版本。

## 功能特性

- **前台（前后端分离展示）**
  - 首页文章卡片流（Bootstrap 栅格两列布局）
  - 文章详情：mistune 解析 Markdown + 嵌套评论区 + 图片懒加载
  - 分类 / 标签页、文章归档（按年-月分组）、时间轴、友链页
  - 独立页面（自定义页面，如关于/友链等非文章内容）
  - 全文搜索（SQLite FTS5 全文索引，标题 / 正文 / 摘要）
  - RSS 2.0（`/feed.xml`）与 Atom 1.0（`/feed.atom`）订阅
  - 中英双语界面（cookie 记忆语言偏好，前台文案可切换）
  - 评论反垃圾：蜜罐字段 + IP 频率限制 + 垃圾关键词过滤
  - 侧边栏：个人资料、最新文章、热门文章、分类、标签云
- **后台管理（`/admin`）**
  - Session-Cookie 单用户登录（默认 `admin / admin123`）
  - 文章编辑：textarea 写 Markdown + 实时预览
  - 独立页面管理（新建 / 编辑 / 删除）
  - 评论审核（通过 / 驳回 / 删除）
  - 站点设置表单：站点信息、主题、语言、评论开关、通知配置等，存 `options` 表
  - 通知设置：Bark 推送 + 邮件（SMTP）通知配置入口
  - 友链管理、分类管理
- **技术亮点**
  - Jinja2 模板继承 + 组件拆分（components/）
  - CSS 变量驱动多配色 + 深色 / 浅色模式切换（跟随系统 / 手动）
  - SQLite FTS5 全文搜索 + 触发器自动同步文章索引
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
├── models/          # SQLAlchemy 7 张表模型
├── schemas/         # Pydantic 校验
├── routers/         # 前台 / 后台 / API 路由分离
├── utils/           # Markdown / 搜索 / RSS·Atom / 反垃圾 / i18n / 通知 / 钩子
├── templates/
│   ├── base.html               # 基础骨架
│   ├── components/             # header/nav/sidebar/footer/card/comments
│   └── pages/                  # 首页·详情·分类·标签·归档·时间轴·友链·搜索·独立页面·后台
└── static/          # 静态资源（CSS/JS/本地 Bootstrap）
run.py               # 开发启动脚本
requirements.txt
```

## 数据模型（7 表）

`users` · `articles` · `categories` · `tags` · `comments`（自引用嵌套）· `options`（站点配置键值对，含友链 JSON）· `pages`（独立页面）

> 文章全文搜索基于 SQLite FTS5 虚拟表 `articles_fts`，由触发器在文章增删改时自动同步。

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
| `DEBUG` | `false` | 调试模式（生产环境保持关闭）|

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

### v0.0.5（2026-08-04）
- **修复**：通知邮件中文章链接为相对路径，现已传入 `base_url` 生成完整 URL
- **修复**：文章详情页阅读量 "阅读" 硬编码中文，改为 `t('views')` 支持 i18n
- **修复**：Pjax 导航后"取消回复"按钮事件丢失，改用事件委托兼容 DOM 替换
- **修复**：`ga_code`（Google Analytics）设置项存在但从未渲染，现已注入 `base.html` 的 `<head>`

### v0.0.4（2026-08-04）
- **安全加固**：登录接口（`/admin/login` + `/api/auth/login`）增加 IP 滑动窗口限流防暴力破解
- **安全加固**：Markdown 链接/图片增加 URL 协议白名单，仅允许 `http/https/mailto/tel/ftp`，阻断 `javascript:` XSS
- **安全加固**：`DEBUG` 默认为 `false`（生产默认安全），启动时输出安全提醒（默认密钥/密码）
- **性能优化**：站点全量配置 (`get_options_dict`) 增加 TTL 缓存，避免每次查库
- **性能优化**：侧边栏数据 (`_sidebar_data`) 增加 TTL 缓存；标签频次统计仅拉 `_tags` 字段，减少内存开销
- **性能优化**：分类页 / 标签页增加分页（每页 `PAGE_SIZE` 篇），避免一次性加载全量文章
- **性能优化**：标签页改用 SQL `LIKE` 过滤代替全量加载后 Python 过滤，大幅降低查询时间
- **性能优化**：仪表盘总阅读量改用 `func.sum` 聚合，避免加载所有文章到内存
- **前端修复**：标签链接做 `slug` 化 + URL 编码，修复含空格/特殊字符标签链接断裂问题
- 缓存失效策略：配置写入时自动失效缓存，保证数据一致性

### v0.0.3（2026-08-04）
- 新增 RSS 2.0（`/feed.xml`）与 Atom 1.0（`/feed.atom`）订阅，`app/utils/feed.py` 标准库生成 XML
- 新增独立页面模型 `pages` 与前台 `/page/{slug}`、后台页面管理
- 新增全文搜索：SQLite FTS5 虚拟表 + 触发器自动同步，失败回退 LIKE，`app/utils/search.py`
- 评论加入反垃圾：蜜罐字段 + IP 频率限制 + 垃圾关键词过滤，`app/utils/anti_spam.py`
- 新增中英双语支持：`app/utils/i18n.py` 翻译字典 + cookie 记忆语言偏好，前台文案可切换
- 完善亮暗模式：跟随系统 / 手动切换，CSS 变量驱动
- 开源协议改为 GPLv3（`LICENSE`）
- 修复 404 渲染状态码、API 评论缺 `Request` 导入、FTS 初始化等逻辑问题

### v0.0.2（2026-08-04）
- 新增评论通知模块 `app/utils/notify.py`：Bark 推送 + SMTP 邮件发送
- 用户发表评论 → Bark 推送通知管理员（失败静默，不影响主流程）
- 管理员回复评论 → 邮件通知被回复的用户（需用户填写邮箱）
- 后台设置新增「通知设置」卡片：Bark / 邮件（SMTP）开关与配置项
- 通过 hooks 机制接入评论事件，代码解耦，可扩展其他通知渠道

### v0.0.1（2026-08-04）
- 搭建完整项目骨架：`app/` 分层（core / models / schemas / routers / utils）
- 实现 6 表模型与基础数据初始化
- 完成前台页面：首页、文章详情、分类、标签、归档、时间轴、友链、搜索
- 完成后台管理：登录、文章 CRUD、评论审核、站点设置、友链、分类
- 实现主题系统（CSS 变量 + 深色/浅色 + 多配色）、毛玻璃顶栏、Pjax、图片懒加载
- 集成 mistune Markdown 渲染与嵌套评论
- 提供 `/api` JSON 接口（JWT 认证）演示前后端分离

## License

[GNU GPL v3.0](LICENSE)
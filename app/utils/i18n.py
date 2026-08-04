"""中英双语支持。

提供翻译字典与 `t()` 翻译函数，语言通过 cookie（`lang`）或站点配置决定。
模板中通过 `t(key)` 与 `lang` 使用。
"""

SUPPORTED_LANGS = ("zh", "en")

# 界面文案
TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh": {
        "nav_home": "首页",
        "nav_archive": "归档",
        "nav_timeline": "时间轴",
        "nav_links": "友链",
        "nav_search": "搜索",
        "nav_admin": "管理",
        "nav_pages": "页面",
        "latest_articles": "最新文章",
        "hot_articles": "热门文章",
        "categories": "分类",
        "tags": "标签",
        "no_articles": "暂无文章",
        "no_tags": "暂无标签",
        "no_categories": "暂无分类",
        "comments": "评论",
        "comment_disabled": "评论已关闭。",
        "comment_placeholder": "写下你的评论…",
        "reply_placeholder": "回复 @{name}：",
        "name": "昵称 *",
        "email": "邮箱（可选）",
        "submit_comment": "提交评论",
        "reply": "回复",
        "cancel_reply": "取消回复",
        "no_comments": "还没有评论，来抢沙发吧～",
        "search": "搜索",
        "search_placeholder": "输入关键词搜索文章…",
        "search_no_result": "没有找到与「{q}」相关的文章",
        "search_result_count": "共找到 {n} 篇相关文章",
        "read": "阅读",
        "views": "阅读",
        "back_top": "返回顶部",
        "switch_theme": "切换主题",
        "publish": "发布",
        "published": "发布",
        "draft": "草稿",
        "save": "保存",
        "cancel": "取消",
        "edit": "编辑",
        "delete": "删除",
        "dashboard": "仪表盘",
        "articles": "文章管理",
        "write_article": "写文章",
        "comments_manage": "评论审核",
        "settings": "站点设置",
        "links_manage": "友链管理",
        "pages_manage": "页面管理",
        "view_front": "查看前台",
        "logout": "退出登录",
        "powered_by": "Powered by FastAPI · Anncix Blog",
    },
    "en": {
        "nav_home": "Home",
        "nav_archive": "Archive",
        "nav_timeline": "Timeline",
        "nav_links": "Links",
        "nav_search": "Search",
        "nav_admin": "Admin",
        "nav_pages": "Pages",
        "latest_articles": "Latest Articles",
        "hot_articles": "Hot Articles",
        "categories": "Categories",
        "tags": "Tags",
        "no_articles": "No articles yet",
        "no_tags": "No tags",
        "no_categories": "No categories",
        "comments": "Comments",
        "comment_disabled": "Comments are disabled.",
        "comment_placeholder": "Write your comment…",
        "reply_placeholder": "Reply @{name}:",
        "name": "Name *",
        "email": "Email (optional)",
        "submit_comment": "Submit",
        "reply": "Reply",
        "cancel_reply": "Cancel",
        "no_comments": "No comments yet. Be the first!",
        "search": "Search",
        "search_placeholder": "Search articles…",
        "search_no_result": "No articles found for “{q}”",
        "search_result_count": "{n} article(s) found",
        "read": "read",
        "views": "views",
        "back_top": "Back to top",
        "switch_theme": "Toggle theme",
        "publish": "Publish",
        "published": "Published",
        "draft": "Draft",
        "save": "Save",
        "cancel": "Cancel",
        "edit": "Edit",
        "delete": "Delete",
        "dashboard": "Dashboard",
        "articles": "Articles",
        "write_article": "Write",
        "comments_manage": "Comments",
        "settings": "Settings",
        "links_manage": "Links",
        "pages_manage": "Pages",
        "view_front": "View site",
        "logout": "Logout",
        "powered_by": "Powered by FastAPI · Anncix Blog",
    },
}


def normalize_lang(lang: str | None) -> str:
    """规范化语言代码，非法值回退到 zh。"""
    if lang and lang.lower() in SUPPORTED_LANGS:
        return lang.lower()
    return "zh"


def t(lang: str, key: str, **kwargs) -> str:
    """翻译：取当前语言文案，缺失退回中文，再缺失返回 key。"""
    table = TRANSLATIONS.get(lang, TRANSLATIONS["zh"])
    text = table.get(key) or TRANSLATIONS["zh"].get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
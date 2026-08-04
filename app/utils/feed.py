"""RSS 2.0 与 Atom 1.0 订阅源生成。

使用标准库生成 XML 字符串，避免额外依赖。返回 `Response`（`application/xml`）。
"""
import html
from datetime import datetime, timezone

from fastapi.responses import Response

from app.utils.markdown import render_markdown

# 常用时间格式
_RFC822 = "%a, %d %b %Y %H:%M:%S GMT"  # RSS
_ISO8601 = "%Y-%m-%dT%H:%M:%SZ"        # Atom


def _fmt(dt: datetime | None, fmt: str) -> str:
    if not dt:
        dt = datetime.utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(fmt)


def _xml(text: str) -> str:
    """转义 XML 特殊字符。"""
    return html.escape(text or "", quote=True)


def build_rss(base_url: str, site: dict, articles: list) -> str:
    """生成 RSS 2.0 文档。"""
    items = []
    for a in articles:
        link = f"{base_url}/article/{a.slug}"
        summary = a.summary or render_markdown(a.content)[:200]
        items.append(
            "    <item>\n"
            f"      <title>{_xml(a.title)}</title>\n"
            f"      <link>{_xml(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{_xml(link)}</guid>\n"
            f"      <pubDate>{_fmt(a.published_at, _RFC822)}</pubDate>\n"
            f"      <description>{_xml(summary)}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{_xml(site.get('site_name', ''))}</title>\n"
        f"    <link>{_xml(base_url)}</link>\n"
        f"    <description>{_xml(site.get('site_desc', ''))}</description>\n"
        f"    <language>{'en' if site.get('lang') == 'en' else 'zh-cn'}</language>\n"
        f"    <lastBuildDate>{_fmt(None, _RFC822)}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>"
    )


def build_atom(base_url: str, site: dict, articles: list) -> str:
    """生成 Atom 1.0 文档。"""
    entries = []
    for a in articles:
        link = f"{base_url}/article/{a.slug}"
        summary = a.summary or render_markdown(a.content)[:200]
        entries.append(
            "  <entry>\n"
            f"    <title>{_xml(a.title)}</title>\n"
            f"    <link href=\"{_xml(link)}\"/>\n"
            f"    <id>{_xml(link)}</id>\n"
            f"    <updated>{_fmt(a.updated_at or a.published_at, _ISO8601)}</updated>\n"
            f"    <published>{_fmt(a.published_at, _ISO8601)}</published>\n"
            f"    <summary>{_xml(summary)}</summary>\n"
            "  </entry>"
        )
    self_link = f"{base_url}/feed.atom"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f"  <title>{_xml(site.get('site_name', ''))}</title>\n"
        f"  <subtitle>{_xml(site.get('site_desc', ''))}</subtitle>\n"
        f"  <link href=\"{_xml(base_url)}\"/>\n"
        f"  <link rel=\"self\" href=\"{_xml(self_link)}\"/>\n"
        f"  <id>{_xml(base_url)}</id>\n"
        f"  <updated>{_fmt(None, _ISO8601)}</updated>\n"
        + "\n".join(entries)
        + "\n</feed>"
    )


def feed_response(kind: str, base_url: str, site: dict, articles: list) -> Response:
    """返回 RSS 或 Atom 的 XML 响应。kind: 'rss' | 'atom'。"""
    if kind == "atom":
        body = build_atom(base_url, site, articles)
    else:
        body = build_rss(base_url, site, articles)
    return Response(content=body, media_type="application/xml; charset=utf-8")
"""Markdown 解析与渲染工具。"""
import html

import mistune

from mistune import HTMLRenderer

# 自定义渲染器：为外链加 target=_blank，为图片加懒加载
class BlogRenderer(HTMLRenderer):
    def _esc(self, s: str) -> str:
        return html.escape(s or "", quote=True)

    def image(self, text, url, title=None, **kwargs):
        attrs = f'src="{self._esc(url)}" alt="{self._esc(text)}" loading="lazy"'
        if title:
            attrs += f' title="{self._esc(title)}"'
        return f'<img {attrs}/>'

    def link(self, text, url, title=None, **kwargs):
        attrs = f'href="{self._esc(url)}"'
        if url.startswith("http"):
            attrs += ' target="_blank" rel="noopener noreferrer"'
        if title:
            attrs += f' title="{self._esc(title)}"'
        return f'<a {attrs}>{text}</a>'


_markdown = mistune.create_markdown(renderer=BlogRenderer())


def render_markdown(text: str | None) -> str:
    """将 Markdown 文本渲染为安全 HTML。"""
    return _markdown(text or "")


def extract_summary(text: str | None, length: int = 120) -> str:
    """从 Markdown 原文提取纯文本摘要。"""
    content = (text or "").strip()
    if not content:
        return ""
    # 去掉 markdown 语法符号，保留纯文本
    import re

    plain = re.sub(r"[#>*`~\[\]()!-]", "", content)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:length] + ("…" if len(plain) > length else "")
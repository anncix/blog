"""钩子机制预留：可用于主题扩展 / 事件通知 / 插值替换。

当前为最小实现，提供注册与触发的空壳，后续可扩展
（如文章发布后推送、评论过滤等）。
"""


class HookManager:
    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def register(self, event: str, handler) -> None:
        """注册事件处理器。"""
        self._handlers.setdefault(event, []).append(handler)

    def trigger(self, event: str, context: dict | None = None) -> dict:
        """触发事件，返回上下文（可被处理器修改）。"""
        context = context or {}
        for handler in self._handlers.get(event, []):
            result = handler(context)
            if result is not None:
                context = result
        return context


hooks = HookManager()
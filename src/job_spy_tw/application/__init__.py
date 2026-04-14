"""Application-layer interfaces for core use cases."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "AssistantApplication",
    "AssistantAgentApplication",
    "CrawlApplication",
    "QueryApplication",
    "ResumeApplication",
]

_ATTRIBUTE_MODULES = {
    "AssistantApplication": ".assistant",
    "AssistantAgentApplication": ".assistant_agent",
    "CrawlApplication": ".crawl",
    "QueryApplication": ".query",
    "ResumeApplication": ".resume",
}


def __getattr__(name: str):
    module_name = _ATTRIBUTE_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name, __name__)
    return getattr(module, name)

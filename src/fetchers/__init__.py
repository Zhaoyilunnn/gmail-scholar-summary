"""Fetcher 模块.

提供论文信息获取功能.
"""

from .base import PaperFetchError, PaperFetcher, PaperInfo
from .simple_html_fetcher import SimpleHTMLFetcher

__all__ = [
    "PaperFetcher",
    "PaperInfo",
    "PaperFetchError",
    "SimpleHTMLFetcher",
]

# 可选导入 DoclingFetcher
try:
    from .docling_fetcher import DoclingFetcher

    __all__.append("DoclingFetcher")
except ImportError:
    pass

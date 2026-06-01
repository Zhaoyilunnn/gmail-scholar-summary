"""Fetcher 模块.

提供论文信息获取功能.
"""

import importlib.util

from .base import PaperFetchError, PaperFetcher, PaperInfo
from .acm_fetcher import ACMFetcher
from .composite_fetcher import CompositeFetcher
from .ieee_fetcher import IEEEFetcher
from .simple_html_fetcher import SimpleHTMLFetcher

__all__ = [
    "PaperFetcher",
    "PaperInfo",
    "PaperFetchError",
    "ACMFetcher",
    "CompositeFetcher",
    "IEEEFetcher",
    "SimpleHTMLFetcher",
]

# 可选导入 DoclingFetcher
if importlib.util.find_spec("docling") is not None:
    from .docling_fetcher import DoclingFetcher  # noqa: F401

    __all__.append("DoclingFetcher")

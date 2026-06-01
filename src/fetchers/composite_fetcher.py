"""组合式论文解析器."""

import logging
from typing import List, Optional

from .acm_fetcher import ACMFetcher
from .base import PaperFetchError, PaperFetcher, PaperInfo
from .ieee_fetcher import IEEEFetcher
from .simple_html_fetcher import SimpleHTMLFetcher
from .url_processors import URLProcessorChain, default_processor_chain

logger = logging.getLogger(__name__)


class CompositeFetcher(PaperFetcher):
    """按 URL 路由到具体 Fetcher 的组合解析器."""

    def __init__(
        self,
        fetchers: Optional[List[PaperFetcher]] = None,
        url_processor: Optional[URLProcessorChain] = None,
    ):
        """初始化 CompositeFetcher.

        Args:
            fetchers: 具体 Fetcher 列表，按顺序匹配.
            url_processor: URL 处理器链，默认使用内置处理器.
        """
        self.fetchers = fetchers or self.default_fetchers()
        self.url_processor = url_processor or default_processor_chain

    @staticmethod
    def default_fetchers() -> List[PaperFetcher]:
        """创建默认 Fetcher 列表.

        Returns:
            默认 Fetcher 列表.
        """
        return [
            SimpleHTMLFetcher(),
            ACMFetcher(),
            IEEEFetcher(),
        ]

    def can_fetch(self, url: str) -> bool:
        """检查是否存在可处理该 URL 的 Fetcher.

        Args:
            url: 待检查的 URL.

        Returns:
            是否可以处理.
        """
        processed_url = self.url_processor.process(url)
        return any(fetcher.can_fetch(processed_url) for fetcher in self.fetchers)

    def fetch(self, url: str) -> PaperInfo:
        """按 URL 路由到第一个匹配的 Fetcher.

        Args:
            url: 论文页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 没有可处理 URL 的 Fetcher 或具体 Fetcher 失败.
        """
        processed_url = self.url_processor.process(url)
        if processed_url != url:
            logger.info(f"URL 已转换: {url[:60]}... -> {processed_url[:60]}...")

        for fetcher in self.fetchers:
            if fetcher.can_fetch(processed_url):
                logger.debug(f"使用 {fetcher.__class__.__name__} 处理: {processed_url}")
                return fetcher.fetch(processed_url)

        raise PaperFetchError(f"不支持的 URL: {processed_url}")

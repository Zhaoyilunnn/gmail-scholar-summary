"""组合式论文解析器."""

import logging
from typing import List, Optional

from .acm_fetcher import ACMFetcher
from .base import PaperFetchError, PaperFetcher, PaperInfo
from .ieee_fetcher import IEEEFetcher
from .metadata_fetcher import MetadataFetcher
from .simple_html_fetcher import SimpleHTMLFetcher
from .url_processors import ProcessedURL, URLProcessorChain, default_processor_chain

logger = logging.getLogger(__name__)


class CompositeFetcher(PaperFetcher):
    """按 URL 路由到具体 Fetcher 的组合解析器."""

    def __init__(
        self,
        fetchers: Optional[List[PaperFetcher]] = None,
        metadata_fetcher: Optional[MetadataFetcher] = None,
        url_processor: Optional[URLProcessorChain] = None,
    ):
        """初始化 CompositeFetcher.

        Args:
            fetchers: 具体 Fetcher 列表，按顺序匹配.
            metadata_fetcher: 公开元数据源 Fetcher.
            url_processor: URL 处理器链，默认使用内置处理器.
        """
        self.fetchers = fetchers or self.default_fetchers()
        self.metadata_fetcher = metadata_fetcher or MetadataFetcher()
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
        processed = self.url_processor.process_with_metadata(url)
        return self.fetch_processed(processed)

    def fetch_processed(self, processed: ProcessedURL) -> PaperInfo:
        """按处理后的 URL 和元数据提示获取论文信息.

        Args:
            processed: 处理后的 URL 信息.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 所有获取方式均失败.
        """
        processed_url = processed.url
        title_hint = processed.title_hint
        original_error = None

        logger.debug(f"处理规范化 URL: {processed_url[:60]}...")

        for fetcher in self.fetchers:
            if fetcher.can_fetch(processed_url):
                logger.debug(f"使用 {fetcher.__class__.__name__} 处理: {processed_url}")
                try:
                    return fetcher.fetch(processed_url)
                except PaperFetchError as e:
                    original_error = e
                    logger.warning(
                        f"页面解析失败，尝试公开元数据源: {processed_url} - {e}"
                    )
                    break

        try:
            return self.metadata_fetcher.fetch(processed_url, title_hint=title_hint)
        except PaperFetchError as metadata_error:
            if original_error is not None:
                raise PaperFetchError(
                    f"{original_error}; fallback 失败: {metadata_error}"
                )
            raise PaperFetchError(f"不支持的 URL: {processed_url}; {metadata_error}")

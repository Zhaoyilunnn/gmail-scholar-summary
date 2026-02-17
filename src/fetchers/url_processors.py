"""URL 处理器模块.

提供论文 URL 的解析和转换功能.
支持从 Google Scholar 重定向链接提取实际 URL,
以及将 arXiv PDF 链接转换为 Abstract 页面.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)


class URLProcessor(ABC):
    """URL 处理器抽象基类.

    所有具体的 URL 处理器都需要继承此类.
    """

    @abstractmethod
    def can_process(self, url: str) -> bool:
        """检查是否能处理该 URL.

        Args:
            url: 待检查的 URL.

        Returns:
            是否能处理.
        """
        pass

    @abstractmethod
    def process(self, url: str) -> str:
        """处理 URL.

        Args:
            url: 原始 URL.

        Returns:
            处理后的 URL.
        """
        pass


class GoogleScholarProcessor(URLProcessor):
    """Google Scholar 重定向链接处理器.

    从 scholar.google.com/scholar_url?url=xxx 格式的链接中提取实际 URL.
    """

    def can_process(self, url: str) -> bool:
        """检查是否是 Google Scholar 重定向链接."""
        return "scholar.google.com/scholar_url" in url

    def process(self, url: str) -> str:
        """提取 scholar_url 中的实际 URL 参数.

        Args:
            url: Google Scholar 重定向 URL.

        Returns:
            提取后的实际 URL.

        Example:
            >>> processor = GoogleScholarProcessor()
            >>> url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/1234"
            >>> processor.process(url)
            'https://arxiv.org/pdf/1234'
        """
        try:
            # 解析 URL
            parsed = urlparse(url)

            # 从查询参数中提取 url
            from urllib.parse import parse_qs

            query_params = parse_qs(parsed.query)

            if "url" in query_params:
                actual_url = query_params["url"][0]
                # URL decode
                actual_url = unquote(actual_url)
                logger.debug(f"从 Google Scholar 提取 URL: {actual_url}")
                return actual_url

        except Exception as e:
            logger.warning(f"解析 Google Scholar URL 失败: {e}, url={url}")

        # 如果解析失败，返回原始 URL
        return url


class ArxivProcessor(URLProcessor):
    """arXiv URL 处理器.

    将 arXiv PDF 链接转换为 Abstract 页面链接.
    """

    # arXiv ID 格式: 4位年份2位月份.5位序号 (如 2401.12345)
    ARXIV_ID_PATTERN = re.compile(r"(\d{4}\.\d{4,5})")

    def can_process(self, url: str) -> bool:
        """检查是否是 arXiv 链接."""
        return "arxiv.org" in url.lower()

    def process(self, url: str) -> str:
        """将 arXiv PDF 链接转换为 Abstract 页面.

        Args:
            url: arXiv URL (可能是 PDF 或 Abstract 页面).

        Returns:
            arXiv Abstract 页面 URL.

        Example:
            >>> processor = ArxivProcessor()
            >>> processor.process("https://arxiv.org/pdf/2401.12345.pdf")
            'https://arxiv.org/abs/2401.12345'
            >>> processor.process("https://arxiv.org/abs/2401.12345")
            'https://arxiv.org/abs/2401.12345'
        """
        try:
            # 提取 arXiv ID
            match = self.ARXIV_ID_PATTERN.search(url)
            if not match:
                logger.debug(f"无法从 URL 提取 arXiv ID: {url}")
                return url

            arxiv_id = match.group(1)

            # 构建 Abstract 页面 URL
            abs_url = f"https://arxiv.org/abs/{arxiv_id}"

            if "/pdf/" in url:
                logger.debug(f"将 arXiv PDF 转换为 Abstract: {url} -> {abs_url}")
            else:
                logger.debug(f"arXiv URL 无需转换: {abs_url}")

            return abs_url

        except Exception as e:
            logger.warning(f"处理 arXiv URL 失败: {e}, url={url}")
            return url


class URLProcessorChain:
    """URL 处理器链.

    按顺序应用多个处理器,每个处理器决定是否处理 URL.
    """

    def __init__(self, processors: Optional[List[URLProcessor]] = None):
        """初始化处理器链.

        Args:
            processors: 处理器列表,按顺序执行.
        """
        self.processors = processors or []

    def add_processor(self, processor: URLProcessor) -> "URLProcessorChain":
        """添加处理器到链尾.

        Args:
            processor: 要添加的处理器.

        Returns:
            self,支持链式调用.
        """
        self.processors.append(processor)
        return self

    def process(self, url: str) -> str:
        """处理 URL.

        按顺序应用所有处理器,每个处理器决定是否处理.

        Args:
            url: 原始 URL.

        Returns:
            处理后的 URL.
        """
        original_url = url
        current_url = url

        for processor in self.processors:
            if processor.can_process(current_url):
                current_url = processor.process(current_url)
                logger.debug(
                    f"{processor.__class__.__name__} 处理: "
                    f"{original_url[:50]}... -> {current_url[:50]}..."
                )

        return current_url


# 默认处理器链
default_processor_chain = (
    URLProcessorChain()
    .add_processor(GoogleScholarProcessor())
    .add_processor(ArxivProcessor())
)


def process_paper_url(url: str) -> str:
    """处理论文 URL.

    使用默认处理器链处理 URL.

    Args:
        url: 原始论文 URL.

    Returns:
        处理后的 URL.

    Example:
        >>> process_paper_url(
        ...     "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        ... )
        'https://arxiv.org/abs/2401.12345'
    """
    return default_processor_chain.process(url)

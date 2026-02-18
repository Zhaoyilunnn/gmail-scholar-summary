"""链接提取器和过滤器模块.

提供从文本中提取论文链接的功能，并过滤掉非论文链接.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class LinkFilter(ABC):
    """链接过滤器抽象基类.

    用于判断链接是否应该被保留或过滤掉.
    """

    @abstractmethod
    def should_keep(self, url: str) -> bool:
        """判断是否应该保留该链接.

        Args:
            url: 待检查的 URL.

        Returns:
            True 表示保留，False 表示过滤掉.
        """
        pass


class NonPaperLinkFilter(LinkFilter):
    """非论文链接过滤器.

    过滤掉 Google Scholar 的用户操作链接等非论文内容.
    """

    # 非论文链接的特征模式
    NON_PAPER_PATTERNS: List[str] = [
        # FIXME: 检查这些特征是否正确
        # Google Scholar 用户操作链接
        r"scholar\.google\.com/citations",
        r"update_op=",
        r"citsig=",
        r"info=",
        # 搜索页面
        r"scholar\.google\.com/schol[?&]",
        # 用户设置等页面
        r"scholar\.google\.com/scholar_settings",
        r"scholar\.google\.com/citations\?",
    ]

    # 论文链接的正面特征（必须包含其中之一）
    PAPER_INDICATORS: List[str] = [
        r"scholar_url",  # Google Scholar 重定向链接
        r"arxiv\.org/(abs|pdf)/",  # arXiv 论文
    ]

    def should_keep(self, url: str) -> bool:
        """判断是否为论文链接.

        Args:
            url: 待检查的 URL.

        Returns:
            True 如果是论文链接，False 如果不是.
        """
        # 首先检查是否包含非论文特征
        for pattern in self.NON_PAPER_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                logger.debug(f"过滤非论文链接: {url[:60]}... (匹配: {pattern})")
                return False

        # 然后检查是否包含论文特征
        for pattern in self.PAPER_INDICATORS:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # 默认过滤掉（保守策略）
        logger.debug(f"过滤未知链接: {url[:60]}...")
        return False


class LinkExtractor:
    """链接提取器.

    从文本中提取 URL，并应用过滤器筛选论文链接.
    """

    # URL 匹配正则表达式
    URL_PATTERN = r"https?://[^\s<>\"{}|\\^`\[\]]+"

    def __init__(self, filters: Optional[List[LinkFilter]] = None):
        """初始化链接提取器.

        Args:
            filters: 过滤器列表，默认使用 NonPaperLinkFilter.
        """
        self.filters = filters or [NonPaperLinkFilter()]

    def extract_links(self, text: str) -> List[str]:
        """从文本中提取并过滤链接.

        Args:
            text: 文本内容.

        Returns:
            过滤后的 URL 列表.
        """
        # 提取所有 URL
        urls = re.findall(self.URL_PATTERN, text)

        # 清理和去重
        cleaned_urls: Set[str] = set()
        for url in urls:
            # 去除末尾的标点
            url = url.rstrip(".,;:!?)")
            cleaned_urls.add(url)

        # 应用过滤器
        filtered_urls = []
        for url in cleaned_urls:
            # 必须通过所有过滤器
            if all(f.should_keep(url) for f in self.filters):
                filtered_urls.append(url)
            else:
                logger.debug(f"链接被过滤: {url[:60]}...")

        logger.info(
            f"从文本提取到 {len(urls)} 个链接，过滤后剩余 {len(filtered_urls)} 个"
        )
        return filtered_urls


# 默认链接提取器
default_link_extractor = LinkExtractor()


def extract_paper_links(text: str) -> List[str]:
    """从文本中提取论文链接.

    使用默认链接提取器提取论文链接.

    Args:
        text: 文本内容.

    Returns:
        论文链接列表.
    """
    return default_link_extractor.extract_links(text)

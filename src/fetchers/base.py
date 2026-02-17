"""Fetcher 抽象基类.

定义论文获取器的统一接口.
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class PaperInfo:
    """论文信息数据结构."""

    def __init__(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        url: str,
        year: str = "",
        venue: str = "",
    ):
        """初始化论文信息.

        Args:
            title: 论文标题.
            authors: 作者列表.
            abstract: 论文摘要.
            url: 论文 URL.
            year: 发表年份.
            venue: 发表 venues.
        """
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.url = url
        self.year = year
        self.venue = venue

    def to_dict(self) -> Dict:
        """转换为字典."""
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "year": self.year,
            "venue": self.venue,
        }


class PaperFetcher(ABC):
    """论文信息获取器抽象基类.

    所有具体的 fetcher 都需要继承此类并实现 fetch 方法.
    """

    @abstractmethod
    def fetch(self, url: str) -> PaperInfo:
        """从 URL 获取论文信息.

        Args:
            url: 论文页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 获取失败.
        """
        pass

    @abstractmethod
    def can_fetch(self, url: str) -> bool:
        """检查是否可以处理该 URL.

        Args:
            url: 待检查的 URL.

        Returns:
            是否可以处理.
        """
        pass


class PaperFetchError(Exception):
    """论文获取失败错误."""

    pass

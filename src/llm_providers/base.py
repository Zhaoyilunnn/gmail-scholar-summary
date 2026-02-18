"""LLM Provider 抽象基类.

定义 LLM 服务提供商的统一接口.
"""

from abc import ABC, abstractmethod
from typing import Dict


class SummaryResult:
    """摘要结果数据结构."""

    def __init__(
        self,
        summary: str,
        background: str,
        method: str,
        results: str,
        relevance_score: float,
    ):
        """初始化摘要结果.

        Args:
            summary: 一句话总结.
            background: 研究背景.
            method: 核心方法.
            results: 主要结果.
            relevance_score: 相关度评分 1-10.
        """
        self.summary = summary
        self.background = background
        self.method = method
        self.results = results
        self.relevance_score = relevance_score

    def to_dict(self) -> Dict:
        """转换为字典."""
        return {
            "summary": self.summary,
            "background": self.background,
            "method": self.method,
            "results": self.results,
            "relevance_score": self.relevance_score,
        }


class LLMProvider(ABC):
    """LLM Provider 抽象基类.

    所有具体的 LLM Provider 都需要继承此类并实现 summarize 方法.
    """

    @abstractmethod
    def summarize(self, title: str, abstract: str) -> SummaryResult:
        """生成论文中文摘要.

        Args:
            title: 论文标题.
            abstract: 论文摘要.

        Returns:
            SummaryResult 对象.

        Raises:
            LLMError: API 调用失败.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查 Provider 是否可用.

        Returns:
            是否可用.
        """
        pass


class LLMError(Exception):
    """LLM API 错误."""

    pass

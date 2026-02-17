"""论文摘要器模块.

整合 Fetcher 和 LLM Provider 生成论文摘要.
"""

import logging
from typing import Dict, List, Optional

from src.config import LLMConfig
from src.fetchers import PaperFetchError, PaperFetcher, PaperInfo
from src.fetchers.simple_html_fetcher import SimpleHTMLFetcher
from src.llm_providers import LLMError, LLMProvider, SummaryResult
from src.llm_providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class SummarizerError(Exception):
    """摘要器错误."""

    pass


class PaperSummarizer:
    """论文摘要器.

    整合 Fetcher 和 LLM Provider，提供完整的论文摘要功能.
    """

    def __init__(
        self,
        fetcher: Optional[PaperFetcher] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """初始化摘要器.

        Args:
            fetcher: 论文获取器，默认使用 SimpleHTMLFetcher.
            llm_provider: LLM Provider，默认使用 OpenAIProvider.

        Raises:
            SummarizerError: 初始化失败.
        """
        self.fetcher = fetcher or SimpleHTMLFetcher()
        self.llm_provider = llm_provider or OpenAIProvider()

        # 检查 LLM Provider 是否可用
        if not self.llm_provider.is_available():
            raise SummarizerError("LLM Provider 不可用，请检查 API Key 配置")

    def process_url(self, url: str) -> Optional[Dict]:
        """处理单个 URL，获取论文信息并生成摘要.

        Args:
            url: 论文页面 URL.

        Returns:
            包含论文信息和摘要的字典，失败返回 None.
        """
        logger.info(f"处理论文: {url}")

        try:
            # 1. 获取论文信息
            paper_info = self.fetcher.fetch(url)
            logger.debug(f"获取论文信息成功: {paper_info.title}")

            # 2. 生成摘要
            summary = self.llm_provider.summarize(paper_info.title, paper_info.abstract)
            logger.debug(f"生成摘要成功: {summary.summary}")

            # 3. 合并结果
            return {
                **paper_info.to_dict(),
                **summary.to_dict(),
            }

        except PaperFetchError as e:
            logger.error(f"获取论文信息失败: {url} - {e}")
            return None
        except LLMError as e:
            logger.error(f"生成摘要失败: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"处理论文时发生未知错误: {url} - {e}")
            return None

    def process_urls(self, urls: List[str]) -> List[Dict]:
        """批量处理多个 URL.

        Args:
            urls: URL 列表.

        Returns:
            成功处理的论文列表.
        """
        results = []

        for url in urls:
            result = self.process_url(url)
            if result:
                results.append(result)

        logger.info(f"成功处理 {len(results)}/{len(urls)} 篇论文")
        return results

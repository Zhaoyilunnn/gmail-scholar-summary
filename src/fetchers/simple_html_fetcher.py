"""基于 BeautifulSoup 的简单 HTML 解析器.

使用 requests 和 BeautifulSoup 解析论文页面.
"""

import logging
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .base import PaperFetchError, PaperFetcher, PaperInfo
from .url_processors import URLProcessorChain, default_processor_chain

logger = logging.getLogger(__name__)


class SimpleHTMLFetcher(PaperFetcher):
    """基于 BeautifulSoup 的简单 HTML 解析器.

    支持 Google Scholar 和 arXiv 页面解析.
    """

    def __init__(
        self,
        timeout_sec: float = 30.0,
        retry_times: int = 3,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        url_processor: Optional[URLProcessorChain] = None,
    ):
        """初始化 Fetcher.

        Args:
            timeout_sec: 请求超时时间，单位秒.
            retry_times: 重试次数.
            user_agent: User-Agent 字符串.
            url_processor: URL 处理器链，默认使用内置处理器.
        """
        self.timeout_sec = timeout_sec
        self.retry_times = retry_times
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.url_processor = url_processor or default_processor_chain

    def can_fetch(self, url: str) -> bool:
        """检查是否可以处理该 URL.

        Args:
            url: 待检查的 URL.

        Returns:
            是否可以处理.
        """
        return "scholar.google.com" in url or "arxiv.org" in url

    def fetch(self, url: str) -> PaperInfo:
        """从 URL 获取论文信息.

        Args:
            url: 论文页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 获取失败.
        """
        if not self.can_fetch(url):
            raise PaperFetchError(f"不支持的 URL: {url}")

        # 使用处理器链清理和转换 URL
        processed_url = self.url_processor.process(url)
        if processed_url != url:
            logger.info(f"URL 已转换: {url[:60]}... -> {processed_url[:60]}...")

        logger.debug(f"开始获取论文信息: {processed_url}")

        # 重试机制
        last_error = None
        for attempt in range(self.retry_times):
            try:
                response = self.session.get(processed_url, timeout=self.timeout_sec)
                response.raise_for_status()
                return self._parse_html(response.text, processed_url)
            except requests.Timeout:
                last_error = f"请求超时 (尝试 {attempt + 1}/{self.retry_times})"
                logger.warning(f"{last_error}: {processed_url}")
                time.sleep(1 * (attempt + 1))  # 指数退避
            except requests.RequestException as e:
                last_error = f"请求失败: {e}"
                logger.error(f"{last_error}: {processed_url}")
                raise PaperFetchError(f"获取论文失败: {processed_url} - {last_error}")

        raise PaperFetchError(
            f"获取论文失败，已重试 {self.retry_times} 次: {processed_url}"
        )

    def _parse_html(self, html: str, url: str) -> PaperInfo:
        """解析 HTML 提取论文信息.

        Args:
            html: HTML 内容.
            url: 页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 解析失败.
        """
        soup = BeautifulSoup(html, "lxml")

        if "scholar.google.com" in url:
            return self._parse_scholar(soup, url)
        elif "arxiv.org" in url:
            return self._parse_arxiv(soup, url)
        else:
            raise PaperFetchError(f"无法解析 URL: {url}")

    def _parse_scholar(self, soup: BeautifulSoup, url: str) -> PaperInfo:
        """解析 Google Scholar 页面.

        Args:
            soup: BeautifulSoup 对象.
            url: 页面 URL.

        Returns:
            PaperInfo 对象.
        """
        # 尝试多种选择器获取标题
        title = ""
        title_selectors = [
            "h3.gs_rt",  # 搜索结果标题
            "#gsc_vcd_title",  # 详情页标题
            "h1",  # 一般标题
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                # 去除 [PDF] [HTML] 等标签
                title = re.sub(r"\[.*?\]", "", title).strip()
                break

        # 获取作者
        authors = []
        author_selectors = [
            ".gs_a",  # 搜索结果作者信息
            ".gsc_vcd_value",  # 详情页
        ]
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                # 提取作者名（通常以 - 或 , 分隔）
                if " - " in author_text:
                    authors = [
                        a.strip() for a in author_text.split(" - ")[0].split(",")
                    ]
                break

        # 获取摘要
        abstract = ""
        abstract_selectors = [
            ".gs_rs",  # 搜索结果摘要
            ".gsc_vcd_value div",  # 详情页摘要
        ]
        for selector in abstract_selectors:
            abstract_elem = soup.select_one(selector)
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                break

        if not title:
            raise PaperFetchError(f"无法从 Google Scholar 页面提取标题: {url}")

        return PaperInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            url=url,
        )

    def _parse_arxiv(self, soup: BeautifulSoup, url: str) -> PaperInfo:
        """解析 arXiv 页面.

        Args:
            soup: BeautifulSoup 对象.
            url: 页面 URL.

        Returns:
            PaperInfo 对象.
        """
        # 获取标题
        title = ""
        title_elem = soup.select_one("h1.title.mathjax")
        if title_elem:
            title = title_elem.get_text(strip=True)
            # 去除 "Title:" 前缀
            title = re.sub(r"^Title:\s*", "", title)

        # 获取作者
        authors = []
        author_elems = soup.select("div.authors a")
        for elem in author_elems:
            author_name = elem.get_text(strip=True)
            if author_name:
                authors.append(author_name)

        # 获取摘要
        abstract = ""
        abstract_elem = soup.select_one("blockquote.abstract.mathjax")
        if abstract_elem:
            abstract = abstract_elem.get_text(strip=True)
            # 去除 "Abstract:" 前缀
            abstract = re.sub(r"^Abstract:\s*", "", abstract)

        # 获取年份
        year = ""
        dateline_elem = soup.select_one("div.dateline")
        if dateline_elem:
            dateline_text = dateline_elem.get_text(strip=True)
            # 提取年份
            year_match = re.search(r"(\d{4})", dateline_text)
            if year_match:
                year = year_match.group(1)

        if not title:
            raise PaperFetchError(f"无法从 arXiv 页面提取标题: {url}")

        return PaperInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            url=url,
            year=year,
        )

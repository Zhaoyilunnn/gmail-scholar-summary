"""IEEE Xplore 论文解析器."""

import logging
import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .base import PaperFetchError, PaperFetcher, PaperInfo
from .html_metadata import (
    get_all_meta_contents,
    get_meta_content,
    get_text_by_selectors,
    normalize_whitespace,
)

logger = logging.getLogger(__name__)


class IEEEFetcher(PaperFetcher):
    """IEEE Xplore HTML 页面解析器."""

    def __init__(
        self,
        timeout_sec: float = 30.0,
        retry_times: int = 3,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    ):
        """初始化 IEEEFetcher.

        Args:
            timeout_sec: 请求超时时间，单位秒.
            retry_times: 重试次数.
            user_agent: User-Agent 字符串.
        """
        self.timeout_sec = timeout_sec
        self.retry_times = retry_times
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def can_fetch(self, url: str) -> bool:
        """检查是否可以处理 IEEE Xplore document 页面.

        Args:
            url: 待检查的 URL.

        Returns:
            是否可以处理.
        """
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        return host == "ieeexplore.ieee.org" and path.startswith("/document/")

    def fetch(self, url: str) -> PaperInfo:
        """从 IEEE Xplore URL 获取论文信息.

        Args:
            url: IEEE 论文页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 获取或解析失败.
        """
        if not self.can_fetch(url):
            raise PaperFetchError(f"不支持的 IEEE URL: {url}")

        last_error = ""
        for attempt in range(self.retry_times):
            try:
                response = self.session.get(url, timeout=self.timeout_sec)
                response.raise_for_status()
                return self._parse_html(response.text, url)
            except requests.Timeout:
                last_error = f"请求超时 (尝试 {attempt + 1}/{self.retry_times})"
                logger.warning(f"{last_error}: {url}")
                time.sleep(1 * (attempt + 1))
            except requests.RequestException as e:
                last_error = f"请求失败: {e}"
                logger.error(f"{last_error}: {url}")
                raise PaperFetchError(f"获取 IEEE 论文失败: {url} - {last_error}")

        raise PaperFetchError(
            f"获取 IEEE 论文失败，已重试 {self.retry_times} 次: {url}"
        )

    def _parse_html(self, html: str, url: str) -> PaperInfo:
        """解析 IEEE HTML 页面.

        Args:
            html: HTML 内容.
            url: 页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 标题或摘要缺失.
        """
        soup = BeautifulSoup(html, "lxml")

        title = get_meta_content(
            soup,
            ["citation_title", "dc.title", "dc.Title", "og:title"],
        ) or get_text_by_selectors(soup, ["h1.document-title", "h1"])
        title = self._clean_title(title)

        authors = get_all_meta_contents(
            soup,
            ["citation_author", "dc.creator", "dc.Creator"],
        )

        abstract = get_meta_content(
            soup,
            ["citation_abstract", "dc.description", "description", "og:description"],
        ) or get_text_by_selectors(
            soup,
            [
                "div.abstract-text",
                "div.u-mb-1 .abstract-text",
                "section.abstract",
            ],
        )
        abstract = self._clean_abstract(abstract)

        year = self._extract_year(
            get_meta_content(
                soup,
                ["citation_publication_date", "dc.date", "dc.Date"],
            )
        )
        venue = get_meta_content(
            soup,
            [
                "citation_conference_title",
                "citation_journal_title",
                "citation_inbook_title",
            ],
        )
        venue = normalize_whitespace(venue) or "IEEE"

        if not title:
            raise PaperFetchError(f"无法从 IEEE 页面提取标题: {url}")
        if not abstract:
            raise PaperFetchError(f"无法从 IEEE 页面提取摘要: {url}")

        return PaperInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            url=url,
            year=year,
            venue=venue,
        )

    def _clean_title(self, title: str) -> str:
        """清理 IEEE 标题文本.

        Args:
            title: 原始标题.

        Returns:
            清理后的标题.
        """
        title = normalize_whitespace(title)
        title = re.sub(r"\s*\|\s*IEEE.*$", "", title, flags=re.IGNORECASE)
        return title

    def _clean_abstract(self, abstract: str) -> str:
        """清理 IEEE 摘要文本.

        Args:
            abstract: 原始摘要.

        Returns:
            清理后的摘要.
        """
        abstract = normalize_whitespace(abstract)
        return re.sub(r"^Abstract:?\s*", "", abstract, flags=re.IGNORECASE).strip()

    def _extract_year(self, date_text: str) -> str:
        """从日期文本提取年份.

        Args:
            date_text: 日期文本.

        Returns:
            4 位年份，未找到时返回空字符串.
        """
        match = re.search(r"\b(\d{4})\b", date_text)
        return match.group(1) if match else ""

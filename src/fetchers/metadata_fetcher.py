"""公开元数据源论文解析器."""

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse

import requests

from .base import PaperFetchError, PaperInfo
from .html_metadata import is_blocked_text, normalize_whitespace

logger = logging.getLogger(__name__)


class MetadataFetcher:
    """使用 OpenAlex 和 Crossref 查询论文元数据."""

    OPENALEX_WORKS_URL = "https://api.openalex.org/works"
    CROSSREF_WORKS_URL = "https://api.crossref.org/works"

    def __init__(self, timeout_sec: float = 20.0):
        """初始化 MetadataFetcher.

        Args:
            timeout_sec: 请求超时时间，单位秒.
        """
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "gmail-scholar-summary/0.1 "
                    "(https://github.com/Zhaoyilunnn/gmail-scholar-summary)"
                )
            }
        )

    def fetch(
        self,
        url: str,
        title_hint: str = "",
    ) -> PaperInfo:
        """按 DOI 或标题提示查询论文信息.

        Args:
            url: 原始论文 URL.
            title_hint: 标题提示.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 无法获取可信标题和摘要.
        """
        doi = self.extract_doi(url)

        candidates = []
        if doi:
            candidates.extend(
                [
                    self._fetch_openalex_by_doi(doi, url),
                    self._fetch_crossref_by_doi(doi, url),
                ]
            )

        if title_hint:
            candidates.extend(
                [
                    self._fetch_openalex_by_title(title_hint, url),
                    self._fetch_crossref_by_title(title_hint, url),
                ]
            )

        for candidate in candidates:
            if candidate is None:
                continue
            if self._is_valid_candidate(candidate, title_hint):
                return candidate

        raise PaperFetchError(f"无法从公开元数据源获取可信摘要: {url}")

    def extract_doi(self, url: str) -> str:
        """从 URL 提取 DOI.

        Args:
            url: 论文 URL.

        Returns:
            DOI，未找到时返回空字符串.
        """
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path

        if host == "doi.org":
            return path.lstrip("/")

        if host == "dl.acm.org" and path.startswith("/doi/"):
            doi = path.removeprefix("/doi/")
            if doi.startswith("abs/"):
                doi = doi.removeprefix("abs/")
            return doi

        doi_match = re.search(r"10\.\d{4,9}/[^\s?#]+", url)
        return doi_match.group(0) if doi_match else ""

    def _fetch_openalex_by_doi(self, doi: str, source_url: str) -> Optional[PaperInfo]:
        """使用 OpenAlex DOI 查询."""
        api_url = f"{self.OPENALEX_WORKS_URL}/https://doi.org/{quote(doi, safe='')}"
        data = self._get_json(api_url)
        if not data:
            return None
        return self._parse_openalex_work(data, source_url)

    def _fetch_openalex_by_title(
        self, title: str, source_url: str
    ) -> Optional[PaperInfo]:
        """使用 OpenAlex 标题查询."""
        data = self._get_json(
            self.OPENALEX_WORKS_URL,
            params={"search.title": title, "per-page": "5"},
        )
        for work in data.get("results", []) if data else []:
            candidate = self._parse_openalex_work(work, source_url)
            if candidate and self._title_matches(title, candidate.title):
                return candidate
        return None

    def _fetch_crossref_by_doi(self, doi: str, source_url: str) -> Optional[PaperInfo]:
        """使用 Crossref DOI 查询."""
        data = self._get_json(f"{self.CROSSREF_WORKS_URL}/{quote(doi, safe='')}")
        message = data.get("message") if data else None
        if not isinstance(message, dict):
            return None
        return self._parse_crossref_work(message, source_url)

    def _fetch_crossref_by_title(
        self, title: str, source_url: str
    ) -> Optional[PaperInfo]:
        """使用 Crossref 标题查询."""
        data = self._get_json(
            self.CROSSREF_WORKS_URL,
            params={"query.title": title, "rows": "5"},
        )
        items = data.get("message", {}).get("items", []) if data else []
        for item in items:
            candidate = self._parse_crossref_work(item, source_url)
            if candidate and self._title_matches(title, candidate.title):
                return candidate
        return None

    def _get_json(
        self, url: str, params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送 GET 请求并解析 JSON."""
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_sec)
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"元数据请求失败: {url} - {e}")
            return {}
        except ValueError as e:
            logger.warning(f"元数据 JSON 解析失败: {url} - {e}")
            return {}

    def _parse_openalex_work(
        self, work: Dict[str, Any], source_url: str
    ) -> Optional[PaperInfo]:
        """解析 OpenAlex work."""
        title = normalize_whitespace(str(work.get("title") or ""))
        abstract = self._restore_openalex_abstract(
            work.get("abstract_inverted_index") or {}
        )
        authors = [
            normalize_whitespace(
                str(author.get("author", {}).get("display_name") or "")
            )
            for author in work.get("authorships", [])
        ]
        authors = [author for author in authors if author]
        year = str(work.get("publication_year") or "")
        venue = normalize_whitespace(
            str(
                work.get("primary_location", {}).get("source", {}).get("display_name")
                or ""
            )
        )

        if not title:
            return None
        return PaperInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            url=source_url,
            year=year,
            venue=venue,
        )

    def _parse_crossref_work(
        self, work: Dict[str, Any], source_url: str
    ) -> Optional[PaperInfo]:
        """解析 Crossref work."""
        title = self._first_list_value(work.get("title", []))
        abstract = self._strip_xml(str(work.get("abstract") or ""))
        authors = [
            normalize_whitespace(
                " ".join(
                    [
                        str(author.get("given") or ""),
                        str(author.get("family") or ""),
                    ]
                )
            )
            for author in work.get("author", [])
        ]
        authors = [author for author in authors if author]
        year = self._extract_crossref_year(work)
        venue = self._first_list_value(
            work.get("container-title", []) or work.get("event", {}).get("name", [])
        )

        if not title:
            return None
        return PaperInfo(
            title=title,
            authors=authors,
            abstract=abstract,
            url=source_url,
            year=year,
            venue=venue,
        )

    def _restore_openalex_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """从 OpenAlex inverted index 还原摘要."""
        if not inverted_index:
            return ""

        max_index = max(
            position for positions in inverted_index.values() for position in positions
        )
        words = [""] * (max_index + 1)
        for word, positions in inverted_index.items():
            for position in positions:
                words[position] = word

        return normalize_whitespace(" ".join(words))

    def _strip_xml(self, text: str) -> str:
        """清理 Crossref abstract 中的 XML 标签."""
        text = re.sub(r"<[^>]+>", " ", text)
        return normalize_whitespace(text)

    def _extract_crossref_year(self, work: Dict[str, Any]) -> str:
        """从 Crossref 日期字段提取年份."""
        for key in ["published-print", "published-online", "created", "issued"]:
            date_parts = work.get(key, {}).get("date-parts", [])
            if date_parts and date_parts[0]:
                return str(date_parts[0][0])
        return ""

    def _first_list_value(self, value: Any) -> str:
        """从列表字段获取第一个字符串值."""
        if isinstance(value, list) and value:
            return normalize_whitespace(str(value[0]))
        if isinstance(value, str):
            return normalize_whitespace(value)
        return ""

    def _is_valid_candidate(self, candidate: PaperInfo, title_hint: str) -> bool:
        """检查候选元数据是否可信."""
        if not candidate.title or not candidate.abstract:
            return False
        if is_blocked_text(candidate.title) or is_blocked_text(candidate.abstract):
            return False
        if title_hint and not self._title_matches(title_hint, candidate.title):
            return False
        return True

    def _title_matches(self, expected: str, actual: str) -> bool:
        """严格比较标题是否匹配."""
        expected_title = self._normalize_title(expected)
        actual_title = self._normalize_title(actual)
        return bool(expected_title and expected_title == actual_title)

    def _normalize_title(self, title: str) -> str:
        """归一化标题用于严格匹配."""
        title = normalize_whitespace(title).lower()
        title = re.sub(r"[^\w\s]", " ", title)
        return normalize_whitespace(title)

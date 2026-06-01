"""CompositeFetcher 测试."""

from unittest.mock import Mock

import pytest

from src.fetchers import CompositeFetcher, PaperFetchError, PaperInfo
from src.fetchers.url_processors import ProcessedURL


class TestCompositeFetcher:
    """测试 CompositeFetcher."""

    def test_fetch_routes_to_matching_fetcher(self):
        """测试路由到第一个匹配的 Fetcher."""
        first_fetcher = Mock()
        first_fetcher.can_fetch.return_value = False

        second_fetcher = Mock()
        second_fetcher.can_fetch.return_value = True
        second_fetcher.fetch.return_value = PaperInfo(
            title="Paper",
            authors=[],
            abstract="Abstract",
            url="https://dl.acm.org/doi/10.1145/1234567",
        )

        fetcher = CompositeFetcher(fetchers=[first_fetcher, second_fetcher])
        result = fetcher.fetch("https://dl.acm.org/doi/10.1145/1234567")

        assert result.title == "Paper"
        first_fetcher.fetch.assert_not_called()
        second_fetcher.fetch.assert_called_once_with(
            "https://dl.acm.org/doi/10.1145/1234567"
        )

    def test_fetch_processes_scholar_redirect_before_routing(self):
        """测试路由前处理 Google Scholar 重定向."""
        acm_fetcher = Mock()
        acm_fetcher.can_fetch.return_value = True
        acm_fetcher.fetch.return_value = PaperInfo(
            title="ACM Paper",
            authors=[],
            abstract="Abstract",
            url="https://dl.acm.org/doi/10.1145/1234567",
        )

        fetcher = CompositeFetcher(fetchers=[acm_fetcher])
        url = (
            "https://scholar.google.com/scholar_url?"
            "url=https://dl.acm.org/doi/10.1145/1234567"
        )
        fetcher.fetch(url)

        acm_fetcher.can_fetch.assert_called_once_with(
            "https://dl.acm.org/doi/10.1145/1234567"
        )
        acm_fetcher.fetch.assert_called_once_with(
            "https://dl.acm.org/doi/10.1145/1234567"
        )

    def test_can_fetch_true_when_any_fetcher_matches(self):
        """测试任一 Fetcher 匹配时 can_fetch 返回 True."""
        first_fetcher = Mock()
        first_fetcher.can_fetch.return_value = False

        second_fetcher = Mock()
        second_fetcher.can_fetch.return_value = True

        fetcher = CompositeFetcher(fetchers=[first_fetcher, second_fetcher])

        assert fetcher.can_fetch("https://ieeexplore.ieee.org/document/1234567")

    def test_fetch_unsupported_url(self):
        """测试无 Fetcher 支持时抛错."""
        child_fetcher = Mock()
        child_fetcher.can_fetch.return_value = False

        fetcher = CompositeFetcher(fetchers=[child_fetcher])

        with pytest.raises(PaperFetchError, match="不支持的 URL"):
            fetcher.fetch("https://example.com/paper")

    def test_fetch_processed_falls_back_to_metadata(self):
        """测试页面解析失败后 fallback 到元数据源."""
        child_fetcher = Mock()
        child_fetcher.can_fetch.return_value = True
        child_fetcher.fetch.side_effect = PaperFetchError("captcha")

        metadata_fetcher = Mock()
        metadata_fetcher.fetch.return_value = PaperInfo(
            title="Fallback Paper",
            authors=[],
            abstract="Fallback abstract",
            url="https://ieeexplore.ieee.org/abstract/document/1234567/",
        )

        fetcher = CompositeFetcher(
            fetchers=[child_fetcher],
            metadata_fetcher=metadata_fetcher,
        )
        result = fetcher.fetch_processed(
            ProcessedURL(
                url="https://ieeexplore.ieee.org/abstract/document/1234567/",
                title_hint="Fallback Paper",
            )
        )

        assert result.title == "Fallback Paper"
        metadata_fetcher.fetch.assert_called_once_with(
            "https://ieeexplore.ieee.org/abstract/document/1234567/",
            title_hint="Fallback Paper",
        )

"""ACMFetcher 测试."""

from unittest.mock import Mock, patch

import pytest

from src.fetchers import ACMFetcher, PaperFetchError


class TestACMFetcher:
    """测试 ACMFetcher."""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例."""
        return ACMFetcher(timeout_sec=5.0, retry_times=2)

    def test_can_fetch_acm_doi(self, fetcher):
        """测试能识别 ACM DOI 页面."""
        assert fetcher.can_fetch("https://dl.acm.org/doi/10.1145/1234567.8901234")
        assert fetcher.can_fetch("https://dl.acm.org/doi/abs/10.1145/1234567")

    def test_cannot_fetch_non_acm(self, fetcher):
        """测试不能识别非 ACM 论文页面."""
        assert not fetcher.can_fetch("https://doi.org/10.1145/1234567")
        assert not fetcher.can_fetch("https://dl.acm.org/action/doSearch")
        assert not fetcher.can_fetch("https://example.com/doi/10.1145/1234567")

    @patch("src.fetchers.acm_fetcher.requests.Session")
    def test_fetch_acm_success(self, mock_session_class, fetcher):
        """测试成功获取 ACM 页面."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
        <head>
            <meta name="citation_title" content="Test ACM Paper">
            <meta name="citation_author" content="Author One">
            <meta name="citation_author" content="Author Two">
            <meta name="citation_abstract" content="This is an ACM abstract.">
            <meta name="citation_publication_date" content="2024/06/01">
            <meta name="citation_conference_title" content="TestConf 2024">
        </head>
        </html>
        """

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        fetcher.session = mock_session

        result = fetcher.fetch("https://dl.acm.org/doi/10.1145/1234567.8901234")

        assert result.title == "Test ACM Paper"
        assert result.authors == ["Author One", "Author Two"]
        assert result.abstract == "This is an ACM abstract."
        assert result.year == "2024"
        assert result.venue == "TestConf 2024"

    def test_parse_acm_body_fallback(self, fetcher):
        """测试 ACM 正文 selector 兜底解析."""
        html = """
        <html>
        <body>
            <h1 class="citation__title">Fallback ACM Paper | ACM Digital Library</h1>
            <section id="abstract">
                <div class="abstractSection">Abstract This is fallback abstract.</div>
            </section>
        </body>
        </html>
        """

        result = fetcher._parse_html(
            html,
            "https://dl.acm.org/doi/10.1145/1234567",
        )

        assert result.title == "Fallback ACM Paper"
        assert result.abstract == "This is fallback abstract."
        assert result.venue == "ACM"

    def test_parse_acm_missing_title(self, fetcher):
        """测试 ACM 页面缺少标题."""
        html = """
        <html>
        <head>
            <meta name="citation_abstract" content="This is an ACM abstract.">
        </head>
        </html>
        """

        with pytest.raises(PaperFetchError, match="提取标题"):
            fetcher._parse_html(html, "https://dl.acm.org/doi/10.1145/1234567")

    def test_parse_acm_missing_abstract(self, fetcher):
        """测试 ACM 页面缺少摘要."""
        html = """
        <html>
        <head>
            <meta name="citation_title" content="Test ACM Paper">
        </head>
        </html>
        """

        with pytest.raises(PaperFetchError, match="提取摘要"):
            fetcher._parse_html(html, "https://dl.acm.org/doi/10.1145/1234567")

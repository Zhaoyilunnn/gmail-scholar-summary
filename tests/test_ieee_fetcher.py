"""IEEEFetcher 测试."""

from unittest.mock import Mock, patch

import pytest

from src.fetchers import IEEEFetcher, PaperFetchError


class TestIEEEFetcher:
    """测试 IEEEFetcher."""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例."""
        return IEEEFetcher(timeout_sec=5.0, retry_times=2)

    def test_can_fetch_ieee_document(self, fetcher):
        """测试能识别 IEEE document 页面."""
        assert fetcher.can_fetch("https://ieeexplore.ieee.org/document/1234567")
        assert fetcher.can_fetch("https://ieeexplore.ieee.org/document/1234567/")

    def test_cannot_fetch_non_ieee_document(self, fetcher):
        """测试不能识别非 IEEE 论文页面."""
        assert not fetcher.can_fetch("https://ieee.org/document/1234567")
        assert not fetcher.can_fetch(
            "https://ieeexplore.ieee.org/search/searchresult.jsp"
        )
        assert not fetcher.can_fetch("https://example.com/document/1234567")

    @patch("src.fetchers.ieee_fetcher.requests.Session")
    def test_fetch_ieee_success(self, mock_session_class, fetcher):
        """测试成功获取 IEEE 页面."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
        <head>
            <meta name="citation_title" content="Test IEEE Paper">
            <meta name="citation_author" content="Author One">
            <meta name="citation_author" content="Author Two">
            <meta name="citation_abstract" content="This is an IEEE abstract.">
            <meta name="citation_publication_date" content="2024">
            <meta name="citation_conference_title" content="Test IEEE Conference">
        </head>
        </html>
        """

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        fetcher.session = mock_session

        result = fetcher.fetch("https://ieeexplore.ieee.org/document/1234567")

        assert result.title == "Test IEEE Paper"
        assert result.authors == ["Author One", "Author Two"]
        assert result.abstract == "This is an IEEE abstract."
        assert result.year == "2024"
        assert result.venue == "Test IEEE Conference"

    def test_parse_ieee_body_fallback(self, fetcher):
        """测试 IEEE 正文 selector 兜底解析."""
        html = """
        <html>
        <body>
            <h1 class="document-title">Fallback IEEE Paper | IEEE Xplore</h1>
            <div class="abstract-text">Abstract: This is fallback abstract.</div>
        </body>
        </html>
        """

        result = fetcher._parse_html(
            html,
            "https://ieeexplore.ieee.org/document/1234567",
        )

        assert result.title == "Fallback IEEE Paper"
        assert result.abstract == "This is fallback abstract."
        assert result.venue == "IEEE"

    def test_parse_ieee_missing_title(self, fetcher):
        """测试 IEEE 页面缺少标题."""
        html = """
        <html>
        <head>
            <meta name="citation_abstract" content="This is an IEEE abstract.">
        </head>
        </html>
        """

        with pytest.raises(PaperFetchError, match="提取标题"):
            fetcher._parse_html(html, "https://ieeexplore.ieee.org/document/1234567")

    def test_parse_ieee_missing_abstract(self, fetcher):
        """测试 IEEE 页面缺少摘要."""
        html = """
        <html>
        <head>
            <meta name="citation_title" content="Test IEEE Paper">
        </head>
        </html>
        """

        with pytest.raises(PaperFetchError, match="提取摘要"):
            fetcher._parse_html(html, "https://ieeexplore.ieee.org/document/1234567")

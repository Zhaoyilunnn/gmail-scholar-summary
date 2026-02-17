"""Fetcher 模块测试."""

from unittest.mock import Mock, patch

import pytest

from src.fetchers import PaperFetchError, PaperInfo, SimpleHTMLFetcher


class TestPaperInfo:
    """测试 PaperInfo."""

    def test_init(self):
        """测试初始化."""
        info = PaperInfo(
            title="Test Title",
            authors=["Author 1", "Author 2"],
            abstract="Test abstract",
            url="https://example.com/paper",
            year="2024",
            venue="Test Venue",
        )

        assert info.title == "Test Title"
        assert info.authors == ["Author 1", "Author 2"]
        assert info.abstract == "Test abstract"
        assert info.url == "https://example.com/paper"
        assert info.year == "2024"
        assert info.venue == "Test Venue"

    def test_to_dict(self):
        """测试转换为字典."""
        info = PaperInfo(
            title="Test Title",
            authors=["Author 1"],
            abstract="Test abstract",
            url="https://example.com/paper",
        )

        data = info.to_dict()

        assert data["title"] == "Test Title"
        assert data["authors"] == ["Author 1"]
        assert data["abstract"] == "Test abstract"
        assert data["url"] == "https://example.com/paper"


class TestSimpleHTMLFetcher:
    """测试 SimpleHTMLFetcher."""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例."""
        return SimpleHTMLFetcher(timeout_sec=5.0, retry_times=2)

    def test_can_fetch_scholar(self, fetcher):
        """测试能否处理 Google Scholar URL."""
        assert fetcher.can_fetch("https://scholar.google.com/scholar?cluster=123")

    def test_can_fetch_arxiv(self, fetcher):
        """测试能否处理 arXiv URL."""
        assert fetcher.can_fetch("https://arxiv.org/abs/2401.12345")
        assert fetcher.can_fetch("https://arxiv.org/pdf/2401.12345.pdf")

    def test_cannot_fetch_other(self, fetcher):
        """测试不能处理其他 URL."""
        assert not fetcher.can_fetch("https://example.com/paper")
        assert not fetcher.can_fetch("https://ieee.org/document/123")

    def test_fetch_unsupported_url(self, fetcher):
        """测试获取不支持的 URL."""
        with pytest.raises(PaperFetchError, match="不支持的 URL"):
            fetcher.fetch("https://example.com/paper")

    @patch("src.fetchers.simple_html_fetcher.requests.Session")
    def test_fetch_scholar_success(self, mock_session_class, fetcher):
        """测试成功获取 Google Scholar 页面."""
        # 模拟响应
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
        <body>
            <h3 class="gs_rt">Test Paper Title [PDF]</h3>
            <div class="gs_a">Author 1, Author 2 - Journal 2024</div>
            <div class="gs_rs">This is the abstract of the paper.</div>
        </body>
        </html>
        """

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        fetcher.session = mock_session

        result = fetcher.fetch("https://scholar.google.com/scholar?cluster=123")

        assert result.title == "Test Paper Title"
        assert result.authors == ["Author 1", "Author 2"]
        assert result.abstract == "This is the abstract of the paper."

    @patch("src.fetchers.simple_html_fetcher.requests.Session")
    def test_fetch_arxiv_success(self, mock_session_class, fetcher):
        """测试成功获取 arXiv 页面."""
        # 模拟响应
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
        <body>
            <h1 class="title mathjax">Title: Test arXiv Paper</h1>
            <div class="authors">
                <a href="/author/1">Author One</a>
                <a href="/author/2">Author Two</a>
            </div>
            <blockquote class="abstract mathjax">
                Abstract: This is a test abstract for arXiv paper.
            </blockquote>
            <div class="dateline">Submitted on 15 Jan 2024</div>
        </body>
        </html>
        """

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        fetcher.session = mock_session

        result = fetcher.fetch("https://arxiv.org/abs/2401.12345")

        assert result.title == "Test arXiv Paper"
        assert result.authors == ["Author One", "Author Two"]
        assert "test abstract" in result.abstract
        assert result.year == "2024"

    @patch("src.fetchers.simple_html_fetcher.requests.Session")
    def test_fetch_timeout_retry(self, mock_session_class, fetcher):
        """测试超时重试."""
        import requests

        mock_session = Mock()
        mock_session.get.side_effect = requests.Timeout("Request timed out")
        mock_session_class.return_value = mock_session

        fetcher.session = mock_session

        with pytest.raises(PaperFetchError, match="已重试"):
            fetcher.fetch("https://scholar.google.com/scholar?cluster=123")

        # 应该重试 retry_times 次
        assert mock_session.get.call_count == fetcher.retry_times

    @patch("src.fetchers.simple_html_fetcher.requests.Session")
    def test_fetch_missing_title(self, mock_session_class, fetcher):
        """测试页面缺少标题."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html><body>No title here</body></html>"

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        fetcher.session = mock_session

        with pytest.raises(PaperFetchError, match="无法.*提取标题"):
            fetcher.fetch("https://scholar.google.com/scholar?cluster=123")


class TestDoclingFetcher:
    """测试 DoclingFetcher (预留)."""

    def test_not_implemented(self):
        """测试 DoclingFetcher 尚未实现."""
        from src.fetchers.docling_fetcher import DoclingFetcher

        fetcher = DoclingFetcher()

        # 应该提示未安装 docling
        assert not fetcher._docling_available

        # 尝试获取应该抛出错误
        with pytest.raises(PaperFetchError, match="docling 未安装"):
            fetcher.fetch("https://arxiv.org/abs/2401.12345")

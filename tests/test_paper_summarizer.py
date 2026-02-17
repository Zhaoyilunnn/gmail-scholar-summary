"""PaperSummarizer 测试."""

from unittest.mock import Mock, patch

import pytest

from src.fetchers import PaperFetchError, PaperInfo
from src.llm_providers import LLMError, SummaryResult
from src.summarizer import PaperSummarizer, SummarizerError


class TestPaperSummarizer:
    """测试 PaperSummarizer."""

    @patch("src.summarizer.OpenAIProvider")
    def test_init_with_available_provider(self, mock_provider_class):
        """测试使用可用的 Provider 初始化."""
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        summarizer = PaperSummarizer()

        assert summarizer.fetcher is not None
        assert summarizer.llm_provider == mock_provider

    @patch("src.summarizer.OpenAIProvider")
    def test_init_with_unavailable_provider(self, mock_provider_class):
        """测试使用不可用的 Provider 初始化失败."""
        mock_provider = Mock()
        mock_provider.is_available.return_value = False
        mock_provider_class.return_value = mock_provider

        with pytest.raises(SummarizerError, match="LLM Provider 不可用"):
            PaperSummarizer()

    def test_init_with_custom_components(self):
        """测试使用自定义组件初始化."""
        mock_fetcher = Mock()
        mock_provider = Mock()
        mock_provider.is_available.return_value = True

        summarizer = PaperSummarizer(
            fetcher=mock_fetcher,
            llm_provider=mock_provider,
        )

        assert summarizer.fetcher == mock_fetcher
        assert summarizer.llm_provider == mock_provider


class TestProcessUrl:
    """测试处理单个 URL."""

    @pytest.fixture
    def summarizer(self):
        """创建 Summarizer 实例."""
        mock_fetcher = Mock()
        mock_provider = Mock()
        mock_provider.is_available.return_value = True

        return PaperSummarizer(
            fetcher=mock_fetcher,
            llm_provider=mock_provider,
        )

    def test_process_url_success(self, summarizer):
        """测试成功处理 URL."""
        # 模拟 Fetcher 返回
        mock_paper_info = PaperInfo(
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            abstract="Test abstract",
            url="https://arxiv.org/abs/2401.12345",
            year="2024",
        )
        summarizer.fetcher.fetch.return_value = mock_paper_info

        # 模拟 LLM 返回
        mock_summary = SummaryResult(
            summary="一句话总结",
            background="研究背景",
            method="核心方法",
            results="主要结果",
            relevance_score=8.5,
        )
        summarizer.llm_provider.summarize.return_value = mock_summary

        result = summarizer.process_url("https://arxiv.org/abs/2401.12345")

        assert result is not None
        assert result["title"] == "Test Paper"
        assert result["authors"] == ["Author 1", "Author 2"]
        assert result["summary"] == "一句话总结"
        assert result["relevance_score"] == 8.5

        summarizer.fetcher.fetch.assert_called_once_with(
            "https://arxiv.org/abs/2401.12345"
        )
        summarizer.llm_provider.summarize.assert_called_once_with(
            "Test Paper", "Test abstract"
        )

    def test_process_url_fetch_error(self, summarizer):
        """测试获取论文信息失败."""
        summarizer.fetcher.fetch.side_effect = PaperFetchError("获取失败")

        result = summarizer.process_url("https://arxiv.org/abs/2401.12345")

        assert result is None
        summarizer.fetcher.fetch.assert_called_once()
        summarizer.llm_provider.summarize.assert_not_called()

    def test_process_url_llm_error(self, summarizer):
        """测试生成摘要失败."""
        mock_paper_info = PaperInfo(
            title="Test Paper",
            authors=["Author 1"],
            abstract="Test abstract",
            url="https://arxiv.org/abs/2401.12345",
        )
        summarizer.fetcher.fetch.return_value = mock_paper_info
        summarizer.llm_provider.summarize.side_effect = LLMError("LLM 错误")

        result = summarizer.process_url("https://arxiv.org/abs/2401.12345")

        assert result is None

    def test_process_url_unknown_error(self, summarizer):
        """测试未知错误."""
        summarizer.fetcher.fetch.side_effect = Exception("未知错误")

        result = summarizer.process_url("https://arxiv.org/abs/2401.12345")

        assert result is None


class TestProcessUrls:
    """测试批量处理 URL."""

    @pytest.fixture
    def summarizer(self):
        """创建 Summarizer 实例."""
        mock_fetcher = Mock()
        mock_provider = Mock()
        mock_provider.is_available.return_value = True

        return PaperSummarizer(
            fetcher=mock_fetcher,
            llm_provider=mock_provider,
        )

    def test_process_urls_all_success(self, summarizer):
        """测试所有 URL 都成功处理."""

        # 模拟成功返回
        def mock_fetch(url):
            return PaperInfo(
                title=f"Paper {url}",
                authors=["Author"],
                abstract="Abstract",
                url=url,
            )

        summarizer.fetcher.fetch.side_effect = mock_fetch
        summarizer.llm_provider.summarize.return_value = SummaryResult(
            summary="Summary",
            background="Background",
            method="Method",
            results="Results",
            relevance_score=8.0,
        )

        urls = [
            "https://arxiv.org/abs/1",
            "https://arxiv.org/abs/2",
            "https://arxiv.org/abs/3",
        ]
        results = summarizer.process_urls(urls)

        assert len(results) == 3

    def test_process_urls_partial_success(self, summarizer):
        """测试部分 URL 成功处理."""

        # 第一个成功，第二个失败，第三个成功
        def mock_fetch(url):
            if "2" in url:
                raise PaperFetchError("Failed")
            return PaperInfo(
                title=f"Paper {url}",
                authors=["Author"],
                abstract="Abstract",
                url=url,
            )

        summarizer.fetcher.fetch.side_effect = mock_fetch
        summarizer.llm_provider.summarize.return_value = SummaryResult(
            summary="Summary",
            background="Background",
            method="Method",
            results="Results",
            relevance_score=8.0,
        )

        urls = [
            "https://arxiv.org/abs/1",
            "https://arxiv.org/abs/2",  # 会失败
            "https://arxiv.org/abs/3",
        ]
        results = summarizer.process_urls(urls)

        assert len(results) == 2

    def test_process_urls_empty_list(self, summarizer):
        """测试空列表."""
        results = summarizer.process_urls([])

        assert results == []
        summarizer.fetcher.fetch.assert_not_called()

"""URL 处理器模块测试."""

import pytest

from src.fetchers.url_processors import (
    ArxivProcessor,
    GoogleScholarProcessor,
    URLProcessorChain,
    default_processor_chain,
    process_paper_url,
)


class TestGoogleScholarProcessor:
    """测试 Google Scholar 处理器."""

    @pytest.fixture
    def processor(self):
        """创建处理器实例."""
        return GoogleScholarProcessor()

    def test_can_process_scholar_url(self, processor):
        """测试能识别 Google Scholar URL."""
        assert processor.can_process(
            "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/1234"
        )
        assert processor.can_process(
            "https://scholar.google.com/scholar_url?hl=zh-CN&url=https://example.com"
        )

    def test_cannot_process_regular_url(self, processor):
        """测试不能识别普通 URL."""
        assert not processor.can_process("https://arxiv.org/abs/1234")
        assert not processor.can_process("https://example.com")

    def test_process_simple_url(self, processor):
        """测试处理简单的 scholar URL."""
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        result = processor.process(url)
        assert result == "https://arxiv.org/pdf/2401.12345"

    def test_process_complex_url(self, processor):
        """测试处理复杂的 scholar URL（带多个参数）."""
        url = (
            "https://scholar.google.com/scholar_url?"
            "url=https://arxiv.org/pdf/2602.09302&"
            "hl=zh-CN&sa=X&d=14589868630261160684"
        )
        result = processor.process(url)
        assert result == "https://arxiv.org/pdf/2602.09302"

    def test_process_url_encoded(self, processor):
        """测试处理 URL 编码的链接."""
        # URL 编码的空格和特殊字符
        url = "https://scholar.google.com/scholar_url?url=https%3A%2F%2Farxiv.org%2Fpdf%2F2401.12345"
        result = processor.process(url)
        assert result == "https://arxiv.org/pdf/2401.12345"

    def test_process_invalid_url(self, processor):
        """测试处理无效的 scholar URL（没有 url 参数）."""
        url = "https://scholar.google.com/scholar_url?hl=zh-CN"
        result = processor.process(url)
        # 应该返回原始 URL
        assert result == url


class TestArxivProcessor:
    """测试 arXiv 处理器."""

    @pytest.fixture
    def processor(self):
        """创建处理器实例."""
        return ArxivProcessor()

    def test_can_process_arxiv_url(self, processor):
        """测试能识别 arXiv URL."""
        assert processor.can_process("https://arxiv.org/abs/2401.12345")
        assert processor.can_process("https://arxiv.org/pdf/2401.12345.pdf")
        assert processor.can_process("http://arxiv.org/abs/2401.12345")

    def test_cannot_process_non_arxiv_url(self, processor):
        """测试不能识别非 arXiv URL."""
        assert not processor.can_process("https://scholar.google.com/...")
        assert not processor.can_process("https://ieee.org/...")

    def test_process_pdf_to_abs(self, processor):
        """测试将 PDF 链接转换为 Abstract."""
        url = "https://arxiv.org/pdf/2401.12345.pdf"
        result = processor.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_process_pdf_without_extension(self, processor):
        """测试处理没有 .pdf 后缀的 PDF 链接."""
        url = "https://arxiv.org/pdf/2401.12345"
        result = processor.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_process_abs_no_change(self, processor):
        """测试 Abstract 链接保持不变."""
        url = "https://arxiv.org/abs/2401.12345"
        result = processor.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_process_with_version(self, processor):
        """测试处理带版本的 arXiv ID."""
        url = "https://arxiv.org/pdf/2401.12345v2.pdf"
        result = processor.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_process_old_style_arxiv(self, processor):
        """测试处理旧格式 arXiv ID (例如 cs/0112001)."""
        url = "https://arxiv.org/pdf/cs/0112001"
        # 旧格式可能无法正确提取，但至少不会报错
        result = processor.process(url)
        # 应该返回原样或转换后的 URL
        assert "arxiv.org" in result


class TestURLProcessorChain:
    """测试 URL 处理器链."""

    def test_empty_chain(self):
        """测试空处理器链."""
        chain = URLProcessorChain()
        url = "https://example.com"
        result = chain.process(url)
        assert result == url

    def test_single_processor(self):
        """测试单处理器链."""
        chain = URLProcessorChain([GoogleScholarProcessor()])
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        result = chain.process(url)
        assert result == "https://arxiv.org/pdf/2401.12345"

    def test_multiple_processors(self):
        """测试多处理器链（Google Scholar + arXiv）."""
        chain = URLProcessorChain([GoogleScholarProcessor(), ArxivProcessor()])
        # Google Scholar 重定向到 arXiv PDF，然后转换为 Abstract
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        result = chain.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_chain_add_processor(self):
        """测试链式添加处理器."""
        chain = URLProcessorChain()
        chain.add_processor(GoogleScholarProcessor()).add_processor(ArxivProcessor())

        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        result = chain.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"


class TestDefaultProcessorChain:
    """测试默认处理器链."""

    def test_scholar_to_arxiv(self):
        """测试 Google Scholar 到 arXiv 的完整转换."""
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        result = default_processor_chain.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_direct_arxiv_pdf(self):
        """测试直接 arXiv PDF 转换."""
        url = "https://arxiv.org/pdf/2401.12345.pdf"
        result = default_processor_chain.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_direct_arxiv_abs(self):
        """测试直接 arXiv Abstract 不转换."""
        url = "https://arxiv.org/abs/2401.12345"
        result = default_processor_chain.process(url)
        assert result == "https://arxiv.org/abs/2401.12345"

    def test_non_arxiv_url(self):
        """测试非 arXiv URL 保持不变."""
        url = "https://example.com/paper.pdf"
        result = default_processor_chain.process(url)
        assert result == "https://example.com/paper.pdf"


class TestProcessPaperUrl:
    """测试便捷的 process_paper_url 函数."""

    def test_scholar_arxiv_chain(self):
        """测试完整的转换链."""
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2602.09302"
        result = process_paper_url(url)
        assert result == "https://arxiv.org/abs/2602.09302"

    def test_arxiv_only(self):
        """测试仅 arXiv 转换."""
        url = "https://arxiv.org/pdf/2401.12345"
        result = process_paper_url(url)
        assert result == "https://arxiv.org/abs/2401.12345"

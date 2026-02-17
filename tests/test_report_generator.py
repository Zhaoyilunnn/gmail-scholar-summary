"""Report Generator 模块测试."""

import re
from datetime import datetime

import pytest

from src.config import ReportConfig
from src.report_generator import ReportGenerator


class TestReportGenerator:
    """测试 ReportGenerator."""

    @pytest.fixture
    def generator(self):
        """创建 Generator 实例."""
        return ReportGenerator()

    @pytest.fixture
    def sample_papers(self):
        """示例论文数据."""
        return [
            {
                "title": "Test Paper 1",
                "authors": ["Author A", "Author B"],
                "url": "https://arxiv.org/abs/2401.00001",
                "year": "2024",
                "venue": "ICML",
                "summary": "一句话总结1",
                "background": "研究背景1",
                "method": "核心方法1",
                "results": "主要结果1",
                "relevance_score": 8.5,
            },
            {
                "title": "Test Paper 2",
                "authors": ["Author C"],
                "url": "https://arxiv.org/abs/2401.00002",
                "year": "2023",
                "venue": "",
                "summary": "一句话总结2",
                "background": "",
                "method": "核心方法2",
                "results": "",
                "relevance_score": 7.0,
            },
        ]

    def test_init_default_config(self):
        """测试使用默认配置初始化."""
        generator = ReportGenerator()
        assert generator.config is not None
        assert generator.config.format == "markdown"

    def test_init_custom_config(self):
        """测试使用自定义配置初始化."""
        config = ReportConfig(format="html")
        generator = ReportGenerator(config)
        assert generator.config.format == "html"


class TestGenerateMarkdown:
    """测试生成 Markdown 报告."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_papers(self):
        return [
            {
                "title": "Test Paper 1",
                "authors": ["Author A", "Author B"],
                "url": "https://arxiv.org/abs/2401.00001",
                "year": "2024",
                "venue": "ICML",
                "summary": "一句话总结1",
                "background": "研究背景1",
                "method": "核心方法1",
                "results": "主要结果1",
                "relevance_score": 8.5,
            },
        ]

    def test_generate_markdown_with_papers(self, generator, sample_papers):
        """测试生成包含论文的 Markdown 报告."""
        report = generator.generate_markdown(sample_papers)

        # 检查标题
        assert "# 学术周报" in report

        # 检查统计信息
        assert "1** 篇论文" in report or "1" in report

        # 检查论文内容
        assert "Test Paper 1" in report
        assert "Author A, Author B" in report
        assert "一句话总结1" in report
        assert "8.5/10" in report

    def test_generate_markdown_empty(self, generator):
        """测试生成空报告."""
        report = generator.generate_markdown([])

        assert "# 学术周报" in report
        assert "没有新论文" in report

    def test_generate_markdown_no_optional_fields(self, generator):
        """测试论文缺少可选字段."""
        papers = [
            {
                "title": "Minimal Paper",
                "authors": [],
                "url": "",
                "summary": "Summary only",
                "relevance_score": 5.0,
            }
        ]

        report = generator.generate_markdown(papers)

        assert "Minimal Paper" in report
        assert "Summary only" in report


class TestGenerateHtml:
    """测试生成 HTML 报告."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    @pytest.fixture
    def sample_papers(self):
        return [
            {
                "title": "Test Paper 1",
                "authors": ["Author A"],
                "url": "https://arxiv.org/abs/2401.00001",
                "year": "2024",
                "summary": "一句话总结",
                "relevance_score": 8.0,
            },
        ]

    def test_generate_html_with_papers(self, generator, sample_papers):
        """测试生成包含论文的 HTML 报告."""
        report = generator.generate_html(sample_papers)

        # 检查基本结构
        assert "<!DOCTYPE html>" in report
        assert "<html>" in report
        assert "</html>" in report

        # 检查标题
        assert "<title>学术周报" in report
        assert "<h1>学术周报" in report

        # 检查内容
        assert "Test Paper 1" in report
        assert "Author A" in report
        assert "一句话总结" in report

        # 检查样式
        assert "<style>" in report
        assert "</style>" in report

    def test_generate_html_empty(self, generator):
        """测试生成空 HTML 报告."""
        report = generator.generate_html([])

        assert "<!DOCTYPE html>" in report
        assert "没有新论文" in report


class TestFormatPaper:
    """测试格式化单篇论文."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_format_paper_markdown(self, generator):
        """测试 Markdown 格式化."""
        paper = {
            "title": "Test Paper",
            "authors": ["Author 1", "Author 2"],
            "url": "https://example.com",
            "year": "2024",
            "venue": "Test Venue",
            "summary": "Summary",
            "background": "Background",
            "method": "Method",
            "results": "Results",
            "relevance_score": 9.0,
        }

        formatted = generator._format_paper_markdown(1, paper)

        assert "### 1. [Test Paper](https://example.com)" in formatted
        assert "Author 1, Author 2" in formatted
        assert "年份: 2024" in formatted
        assert "发表: Test Venue" in formatted
        assert "Summary" in formatted
        assert "9.0/10" in formatted

    def test_format_paper_html(self, generator):
        """测试 HTML 格式化."""
        paper = {
            "title": "Test Paper",
            "authors": ["Author 1"],
            "url": "https://example.com",
            "year": "2024",
            "summary": "Summary",
            "relevance_score": 8.0,
        }

        formatted = generator._format_paper_html(1, paper)

        assert '<div class="paper">' in formatted
        assert '<h3>1. <a href="https://example.com">Test Paper</a></h3>' in formatted
        assert "Author 1" in formatted
        assert "8.0/10" in formatted

    def test_format_paper_missing_fields(self, generator):
        """测试格式化缺少字段的论文."""
        paper = {
            "title": "Minimal",
            "url": "",
            "relevance_score": 5.0,
        }

        formatted = generator._format_paper_markdown(1, paper)

        assert "Minimal" in formatted
        assert "5.0/10" in formatted
        # 不应该有作者、年份等字段
        assert "作者" not in formatted


class TestEmptyReports:
    """测试空报告生成."""

    def test_empty_markdown_report(self):
        """测试空 Markdown 报告."""
        generator = ReportGenerator()
        report = generator._generate_empty_report()

        assert "# 学术周报" in report
        assert "没有新论文" in report

    def test_empty_html_report(self):
        """测试空 HTML 报告."""
        generator = ReportGenerator()
        report = generator._generate_empty_html_report()

        assert "<!DOCTYPE html>" in report
        assert "没有新论文" in report

"""链接过滤器模块测试."""

import pytest

from src.link_filters import (
    LinkExtractor,
    NonPaperLinkFilter,
    extract_paper_links,
)


class TestNonPaperLinkFilter:
    """测试非论文链接过滤器."""

    @pytest.fixture
    def filter(self):
        """创建过滤器实例."""
        return NonPaperLinkFilter()

    def test_filter_citations_link(self, filter):
        """测试过滤 citations 链接."""
        url = (
            "https://scholar.google.com/citations?hl=zh-CN&update_op=email_library_add"
        )
        assert not filter.should_keep(url)

    def test_filter_update_op_link(self, filter):
        """测试过滤 update_op 链接."""
        url = "https://scholar.google.com/citations?info=xxx&update_op=xxx"
        assert not filter.should_keep(url)

    def test_filter_scholar_search(self, filter):
        """测试过滤 scholar 搜索页面."""
        url = "https://scholar.google.com/scholar?q=machine+learning"
        assert not filter.should_keep(url)

    def test_filter_scholar_settings(self, filter):
        """测试过滤 scholar 设置页面."""
        url = "https://scholar.google.com/scholar_settings"
        assert not filter.should_keep(url)

    def test_keep_scholar_url_link(self, filter):
        """测试保留 scholar_url 链接."""
        url = "https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345"
        assert filter.should_keep(url)

    def test_keep_arxiv_abs_link(self, filter):
        """测试保留 arXiv abstract 链接."""
        url = "https://arxiv.org/abs/2401.12345"
        assert filter.should_keep(url)

    def test_keep_arxiv_pdf_link(self, filter):
        """测试保留 arXiv PDF 链接."""
        url = "https://arxiv.org/pdf/2401.12345.pdf"
        assert filter.should_keep(url)

    def test_keep_acm_doi_link(self, filter):
        """测试保留 ACM DOI 页面链接."""
        url = "https://dl.acm.org/doi/10.1145/1234567.8901234"
        assert filter.should_keep(url)

    def test_keep_ieee_document_link(self, filter):
        """测试保留 IEEE document 页面链接."""
        url = "https://ieeexplore.ieee.org/document/1234567"
        assert filter.should_keep(url)

    def test_keep_ieee_abstract_document_link(self, filter):
        """测试保留 IEEE abstract document 页面链接."""
        url = "https://ieeexplore.ieee.org/abstract/document/1234567/"
        assert filter.should_keep(url)

    def test_keep_scholar_url_to_ieee_abstract_document(self, filter):
        """测试保留指向 IEEE abstract document 的 Scholar 重定向."""
        url = (
            "https://scholar.google.com/scholar_url?"
            "url=https://ieeexplore.ieee.org/abstract/document/1234567/"
        )
        assert filter.should_keep(url)

    def test_filter_scholar_url_to_cleardot_image(self, filter):
        """测试过滤指向 cleardot.gif 的 Scholar 重定向."""
        url = (
            "https://scholar.google.com/scholar_url?"
            "url=https://scholar.google.com/scholar/images/cleardot.gif"
        )
        assert not filter.should_keep(url)

    def test_filter_acm_search_link(self, filter):
        """测试过滤 ACM 搜索页面链接."""
        url = "https://dl.acm.org/action/doSearch?AllField=machine+learning"
        assert not filter.should_keep(url)

    def test_filter_ieee_search_link(self, filter):
        """测试过滤 IEEE 搜索页面链接."""
        url = "https://ieeexplore.ieee.org/search/searchresult.jsp"
        assert not filter.should_keep(url)

    def test_filter_unknown_link(self, filter):
        """测试过滤未知链接（保守策略）."""
        url = "https://example.com/paper.pdf"
        assert not filter.should_keep(url)


class TestLinkExtractor:
    """测试链接提取器."""

    def test_extract_simple_text(self):
        """测试从简单文本提取链接."""
        text = """
        Check out this paper: https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345
        Another one: https://scholar.google.com/citations?update_op=email_library_add
        """
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        # 应该只保留 scholar_url 链接
        assert len(links) == 1
        assert "scholar_url" in links[0]

    def test_extract_multiple_papers(self):
        """测试提取多个论文链接."""
        text = """
        Paper 1: https://scholar.google.com/scholar_url?url=https://arxiv.org/abs/2401.11111
        Paper 2: https://arxiv.org/abs/2401.22222
        Action: https://scholar.google.com/citations?info=xxx&update_op=xxx
        """
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        # 应该保留 2 个论文链接
        assert len(links) == 2
        assert all("arxiv.org" in link or "scholar_url" in link for link in links)

    def test_extract_acm_and_ieee_papers(self):
        """测试提取 ACM 和 IEEE 论文链接."""
        text = """
        ACM: https://dl.acm.org/doi/10.1145/1234567.8901234
        IEEE: https://ieeexplore.ieee.org/document/1234567
        Search: https://ieeexplore.ieee.org/search/searchresult.jsp
        """
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        assert len(links) == 2
        assert any("dl.acm.org/doi/" in link for link in links)
        assert any("ieeexplore.ieee.org/document/" in link for link in links)

    def test_extract_deduplicate(self):
        """测试去重功能."""
        text = """
        Same link appears twice:
        https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345
        https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345
        """
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        # 应该只保留 1 个（去重）
        assert len(links) == 1

    def test_extract_clean_punctuation(self):
        """测试清理末尾标点."""
        text = "Paper: https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345."
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        assert len(links) == 1
        assert not links[0].endswith(".")

    def test_extract_no_links(self):
        """测试没有链接的情况."""
        text = "This is just plain text without any URLs."
        extractor = LinkExtractor()
        links = extractor.extract_links(text)

        assert len(links) == 0


class TestExtractPaperLinks:
    """测试便捷的 extract_paper_links 函数."""

    def test_real_world_example(self):
        """测试真实的邮件内容示例."""
        text = """
        New articles published by researchers you follow

        [PDF] Paper Title Here
        https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2602.09302&hl=zh-CN&sa=X

        [Manage citations] https://scholar.google.com/citations?hl=zh-CN&update_op=email_library_add&info=7NpUAjigecoJ
        """
        links = extract_paper_links(text)

        # 应该只保留论文链接
        assert len(links) == 1
        assert "scholar_url" in links[0]
        assert "arxiv.org" in links[0]

    def test_filter_user_actions(self):
        """测试过滤用户操作链接."""
        text = """
        https://scholar.google.com/citations?hl=zh-CN&update_op=email_library_add&info=xxx&citsig=xxx
        https://scholar.google.com/scholar_url?url=https://arxiv.org/pdf/2401.12345
        https://scholar.google.com/citations?view_op=view_citation&continue=xxx
        """
        links = extract_paper_links(text)

        # 只应该保留 scholar_url 链接
        assert len(links) == 1
        assert "scholar_url" in links[0]

"""MetadataFetcher 测试."""

from src.fetchers import MetadataFetcher


class TestMetadataFetcher:
    """测试 MetadataFetcher."""

    def test_extract_acm_doi(self):
        """测试从 ACM URL 提取 DOI."""
        fetcher = MetadataFetcher()

        doi = fetcher.extract_doi("https://dl.acm.org/doi/10.1145/1234567.8901234")

        assert doi == "10.1145/1234567.8901234"

    def test_extract_acm_abs_doi(self):
        """测试从 ACM abs URL 提取 DOI."""
        fetcher = MetadataFetcher()

        doi = fetcher.extract_doi("https://dl.acm.org/doi/abs/10.1145/1234567")

        assert doi == "10.1145/1234567"

    def test_restore_openalex_abstract(self):
        """测试还原 OpenAlex 摘要."""
        fetcher = MetadataFetcher()

        abstract = fetcher._restore_openalex_abstract(
            {
                "This": [0],
                "is": [1],
                "an": [2],
                "abstract": [3],
            }
        )

        assert abstract == "This is an abstract"

    def test_title_matches_strictly_after_normalization(self):
        """测试标题严格匹配."""
        fetcher = MetadataFetcher()

        assert fetcher._title_matches(
            "Cleaning up the Mess: Re-Evaluating Ramulator 2.0",
            "Cleaning up the Mess: Re-Evaluating Ramulator 2.0",
        )
        assert not fetcher._title_matches(
            "Cleaning up the Mess",
            "A Different Paper",
        )

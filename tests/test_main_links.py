"""main 链接处理测试."""

from main import get_unique_links


def test_get_unique_links_deduplicates_scholar_share_variants():
    """测试 Scholar share 不同分享渠道去重为同一论文 URL."""
    emails = [
        {
            "links": [
                (
                    "https://scholar.google.com/scholar_share?"
                    "ss=fb&url=https://ieeexplore.ieee.org/abstract/document/11527248/&"
                    "rt=Cleaning+up+the+Mess"
                ),
                (
                    "https://scholar.google.com/scholar_share?"
                    "ss=tw&url=https://ieeexplore.ieee.org/abstract/document/11527248/&"
                    "rt=Cleaning+up+the+Mess"
                ),
            ]
        }
    ]

    links = get_unique_links(emails)

    assert len(links) == 1
    assert links[0].url == "https://ieeexplore.ieee.org/abstract/document/11527248/"
    assert links[0].title_hint == "Cleaning up the Mess"


def test_get_unique_links_deduplicates_html_escaped_scholar_share_variants():
    """测试 HTML 转义 Scholar share 链接也能去重."""
    emails = [
        {
            "links": [
                (
                    "https://scholar.google.com/scholar_share?"
                    "hl=en&amp;ss=fb&amp;"
                    "url=https://ieeexplore.ieee.org/abstract/document/11527248/&amp;"
                    "rt=Cleaning+up+the+Mess"
                ),
                (
                    "https://scholar.google.com/scholar_share?"
                    "hl=en&amp;ss=tw&amp;"
                    "url=https://ieeexplore.ieee.org/abstract/document/11527248/&amp;"
                    "rt=Cleaning+up+the+Mess"
                ),
            ]
        }
    ]

    links = get_unique_links(emails)

    assert len(links) == 1
    assert links[0].url == "https://ieeexplore.ieee.org/abstract/document/11527248/"
    assert links[0].title_hint == "Cleaning up the Mess"

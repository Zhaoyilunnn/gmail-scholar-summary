"""真实网页 Fetcher 测试.

默认跳过。需要外网时使用:
RUN_LIVE_TESTS=1 uv run pytest tests/test_live_fetchers.py -m live
"""

import os

import pytest

from src.fetchers import ACMFetcher, IEEEFetcher

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_TESTS") != "1",
        reason="需要 RUN_LIVE_TESTS=1 才运行真实网页测试",
    ),
]


def test_live_acm_fetcher():
    """测试真实 ACM 页面解析."""
    url = os.getenv(
        "LIVE_ACM_URL",
        "https://dl.acm.org/doi/10.1145/3544548.3581078",
    )
    fetcher = ACMFetcher()

    result = fetcher.fetch(url)

    assert result.title
    assert result.abstract


def test_live_ieee_fetcher():
    """测试真实 IEEE 页面解析."""
    url = os.getenv(
        "LIVE_IEEE_URL",
        "https://ieeexplore.ieee.org/document/10106900",
    )
    fetcher = IEEEFetcher()

    result = fetcher.fetch(url)

    assert result.title
    assert result.abstract

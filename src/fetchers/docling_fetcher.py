"""基于 Docling 的高级文档解析器.

使用 Docling 库解析复杂文档，支持 PDF 和高级 HTML 解析.

安装: pip install docling
参考: https://docling-project.github.io/docling/
"""

import logging
from typing import TYPE_CHECKING

from .base import PaperFetchError, PaperFetcher, PaperInfo

if TYPE_CHECKING:
    pass  # 类型检查时的导入

logger = logging.getLogger(__name__)


class DoclingFetcher(PaperFetcher):
    """基于 Docling 的高级文档解析器.

    优势:
    - 更好的 PDF 解析能力
    - 支持复杂页面结构
    - 更好的表格和公式识别

    使用方法:
        1. 安装: pip install docling
        2. 修改 config.yaml:
           fetcher:
             type: "docling"
        3. 自动使用此 Fetcher
    """

    def __init__(
        self,
        timeout_sec: float = 30.0,
        retry_times: int = 3,
    ):
        """初始化 DoclingFetcher.

        Args:
            timeout_sec: 请求超时时间，单位秒.
            retry_times: 重试次数.
        """
        self.timeout_sec = timeout_sec
        self.retry_times = retry_times
        self._docling_available = self._check_docling()

    def _check_docling(self) -> bool:
        """检查 docling 是否已安装."""
        try:
            import docling  # noqa: F401

            return True
        except ImportError:
            logger.warning(
                "docling 未安装，将使用默认的 SimpleHTMLFetcher. "
                "运行: pip install docling 以启用高级功能."
            )
            return False

    def can_fetch(self, url: str) -> bool:
        """检查是否可以处理该 URL.

        Args:
            url: 待检查的 URL.

        Returns:
            是否可以处理.
        """
        if not self._docling_available:
            return False
        # Docling 可以处理多种格式
        return any(
            x in url for x in ["scholar.google.com", "arxiv.org", ".pdf", "doi.org"]
        )

    def fetch(self, url: str) -> PaperInfo:
        """从 URL 获取论文信息.

        Args:
            url: 论文页面 URL.

        Returns:
            PaperInfo 对象.

        Raises:
            PaperFetchError: 获取失败.
        """
        if not self._docling_available:
            raise PaperFetchError("docling 未安装. 运行: pip install docling")

        # TODO: 实现 Docling 解析逻辑
        # 参考代码:
        # from docling.document_converter import DocumentConverter
        # converter = DocumentConverter()
        # result = converter.convert(url)
        # doc = result.document
        # title = doc.title
        # abstract = doc.abstract
        # ...

        raise PaperFetchError(
            "DoclingFetcher 尚未实现. "
            "请先使用 SimpleHTMLFetcher (config.fetcher.type = 'simple_html')"
        )

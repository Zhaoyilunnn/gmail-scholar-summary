"""Google Gemini Provider.

通过 GEMINI_API_KEY 环境变量配置.

安装: pip install google-generativeai
"""

import logging
import os
from typing import TYPE_CHECKING

from .base import LLMError, LLMProvider, SummaryResult

if TYPE_CHECKING:
    pass  # 类型检查时的导入

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini Provider.

    配置项:
        GEMINI_API_KEY: API 密钥

    使用方法:
        1. 安装依赖: pip install google-generativeai
        2. 配置 GitHub Secret: GEMINI_API_KEY
        3. 修改 config.yaml: llm.provider = "gemini"

    注意: 此 Provider 目前为预留接口，尚未完全实现.
    """

    DEFAULT_MODEL = "gemini-pro"

    def __init__(self):
        """初始化 Gemini Provider."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))

        self._client = None
        self._genai_available = self._check_genai()

    def _check_genai(self) -> bool:
        """检查 google-generativeai 是否已安装."""
        try:
            import google.generativeai as genai  # noqa: F401

            return True
        except ImportError:
            logger.warning(
                "google-generativeai 未安装，无法使用 GeminiProvider. "
                "运行: pip install google-generativeai"
            )
            return False

    def is_available(self) -> bool:
        """检查 Provider 是否可用.

        Returns:
            是否有 GEMINI_API_KEY 且已安装依赖.
        """
        if not self._genai_available:
            return False
        return self.api_key is not None and len(self.api_key) > 0

    def _get_client(self):
        """获取或创建 Gemini 客户端.

        Returns:
            Gemini 客户端.

        Raises:
            LLMError: API 密钥未配置或依赖未安装.
        """
        if not self._genai_available:
            raise LLMError(
                "google-generativeai 未安装. 运行: pip install google-generativeai"
            )

        if not self.api_key:
            raise LLMError("GEMINI_API_KEY 未配置，请在 GitHub Secrets 中设置")

        if self._client is None:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
            logger.debug(f"Gemini 客户端已创建: model={self.model}")

        return self._client

    def summarize(self, title: str, abstract: str) -> SummaryResult:
        """生成论文中文摘要.

        Args:
            title: 论文标题.
            abstract: 论文摘要.

        Returns:
            SummaryResult 对象.

        Raises:
            LLMError: API 调用失败.
        """
        # TODO: 实现 Gemini 调用逻辑
        raise LLMError(
            "GeminiProvider 尚未完全实现. "
            "请先使用 OpenAIProvider (config.llm.provider = 'openai')"
        )

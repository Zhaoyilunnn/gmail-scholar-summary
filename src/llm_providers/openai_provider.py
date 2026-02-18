"""OpenAI 兼容接口 Provider.

支持标准 OpenAI API 和兼容接口（如 OpenRouter、中转站等）.
通过 GitHub Secrets 配置:
- OPENAI_API_KEY: API 密钥
- OPENAI_BASE_URL: Base URL（可选，默认 https://api.openai.com/v1）
- OPENAI_MODEL: 模型名称（可选，默认 gpt-4o-mini）
"""

import json
import logging
import os
from typing import Optional

from openai import OpenAI

from .base import LLMError, LLMProvider, SummaryResult

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI 兼容接口 Provider.

    配置项:
        OPENAI_API_KEY: 必需，API 密钥
        OPENAI_BASE_URL: 可选，默认 https://api.openai.com/v1
        OPENAI_MODEL: 可选，默认 gpt-4o-mini

    示例:
        # 标准 OpenAI
        OPENAI_API_KEY=sk-xxx
        OPENAI_MODEL=gpt-4o

        # OpenRouter
        OPENAI_API_KEY=sk-or-xxx
        OPENAI_BASE_URL=https://openrouter.ai/api/v1
        OPENAI_MODEL=anthropic/claude-3.5-sonnet
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self):
        """初始化 OpenAI Provider."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))

        self._client: Optional[OpenAI] = None

    def is_available(self) -> bool:
        """检查 Provider 是否可用.

        Returns:
            是否有 OPENAI_API_KEY.
        """
        return self.api_key is not None and len(self.api_key) > 0

    def _get_client(self) -> OpenAI:
        """获取或创建 OpenAI 客户端.

        Returns:
            OpenAI 客户端.

        Raises:
            LLMError: API 密钥未配置.
        """
        if not self.is_available():
            raise LLMError("OPENAI_API_KEY 未配置，请在 GitHub Secrets 中设置")

        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.debug(f"OpenAI 客户端已创建: {self.base_url}, model={self.model}")

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
        client = self._get_client()

        prompt = self._build_prompt(title, abstract)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位学术研究助手，擅长分析和总结学术论文。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise LLMError("OpenAI API 返回空内容")
            return self._parse_response(content)  # type: ignore

        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise LLMError(f"生成摘要失败: {e}")

    def _build_prompt(self, title: str, abstract: str) -> str:
        """构建 Prompt.

        Args:
            title: 论文标题.
            abstract: 论文摘要.

        Returns:
            Prompt 字符串.
        """
        return f"""请对以下学术论文进行中文总结。

论文标题: {title}
论文摘要: {abstract}

请按以下 JSON 格式输出:
{{
    "summary": "一句话总结（50字以内）",
    "background": "研究背景（100字以内）",
    "method": "核心方法（100字以内）",
    "results": "主要结果（100字以内）"
}}

要求:
1. summary 控制在 50 字以内，概括核心贡献
2. background、method、results 每部分 100 字以内
3. 只输出 JSON，不要有其他内容"""

    def _parse_response(self, content: str) -> SummaryResult:
        """解析 API 响应.

        Args:
            content: API 返回的 JSON 字符串.

        Returns:
            SummaryResult 对象.

        Raises:
            LLMError: 解析失败.
        """
        try:
            data = json.loads(content)

            return SummaryResult(
                summary=data.get("summary", ""),
                background=data.get("background", ""),
                method=data.get("method", ""),
                results=data.get("results", ""),
                relevance_score=None,  # 暂时不启用相关度评分
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, content={content}")
            raise LLMError(f"解析 LLM 响应失败: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"字段解析失败: {e}, content={content}")
            raise LLMError(f"解析 LLM 响应字段失败: {e}")

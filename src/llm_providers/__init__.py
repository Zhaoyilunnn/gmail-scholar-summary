"""LLM Provider 模块.

提供多种 LLM 服务的统一接口.
"""

from .base import LLMError, LLMProvider, SummaryResult
from .openai_provider import OpenAIProvider

__all__ = [
    "LLMProvider",
    "SummaryResult",
    "LLMError",
    "OpenAIProvider",
]

# 可选导入 GeminiProvider
try:
    from .gemini_provider import GeminiProvider

    __all__.append("GeminiProvider")
except ImportError:
    pass

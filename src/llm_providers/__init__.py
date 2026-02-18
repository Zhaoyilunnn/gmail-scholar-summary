"""LLM Provider 模块.

提供多种 LLM 服务的统一接口.
"""

import importlib.util

from .base import LLMError, LLMProvider, SummaryResult
from .openai_provider import OpenAIProvider

__all__ = [
    "LLMProvider",
    "SummaryResult",
    "LLMError",
    "OpenAIProvider",
]

# 可选导入 GeminiProvider
if importlib.util.find_spec("google.generativeai") is not None:
    from .gemini_provider import GeminiProvider  # noqa: F401

    __all__.append("GeminiProvider")

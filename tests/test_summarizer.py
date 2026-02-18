"""LLM Provider 模块测试."""

import json
from unittest.mock import Mock, patch

import pytest

from src.llm_providers import LLMError, OpenAIProvider, SummaryResult


class TestSummaryResult:
    """测试 SummaryResult."""

    def test_init(self):
        """测试初始化."""
        result = SummaryResult(
            summary="一句话总结",
            background="研究背景",
            method="核心方法",
            results="主要结果",
            relevance_score=8.5,
        )

        assert result.summary == "一句话总结"
        assert result.background == "研究背景"
        assert result.method == "核心方法"
        assert result.results == "主要结果"
        assert result.relevance_score == 8.5

    def test_to_dict(self):
        """测试转换为字典."""
        result = SummaryResult(
            summary="Test summary",
            background="Test background",
            method="Test method",
            results="Test results",
            relevance_score=7.0,
        )

        data = result.to_dict()

        assert data["summary"] == "Test summary"
        assert data["relevance_score"] == 7.0


class TestOpenAIProvider:
    """测试 OpenAIProvider."""

    @pytest.fixture
    def provider(self):
        """创建 Provider 实例."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "sk-test123",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "OPENAI_MODEL": "gpt-4o-mini",
            },
        ):
            return OpenAIProvider()

    def test_is_available_with_key(self, provider):
        """测试有 API Key 时可用."""
        assert provider.is_available() is True

    def test_is_available_without_key(self):
        """测试无 API Key 时不可用."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            provider = OpenAIProvider()
            assert provider.is_available() is False

    def test_default_values(self, provider):
        """测试默认值."""
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.model == "gpt-4o-mini"
        assert provider.temperature == 0.3
        assert provider.max_tokens == 1000

    @patch("src.llm_providers.openai_provider.OpenAI")
    def test_summarize_success(self, mock_openai_class, provider):
        """测试成功生成摘要."""
        # 模拟 API 响应
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "summary": "测试总结",
                            "background": "测试背景",
                            "method": "测试方法",
                            "results": "测试结果",
                        }
                    )
                )
            )
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = provider.summarize("Test Title", "Test Abstract")

        assert result.summary == "测试总结"
        assert result.background == "测试背景"
        assert result.method == "测试方法"
        assert result.results == "测试结果"
        assert result.relevance_score is None  # 暂时不启用相关度评分

    @patch("src.llm_providers.openai_provider.OpenAI")
    def test_summarize_api_error(self, mock_openai_class, provider):
        """测试 API 调用失败."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        with pytest.raises(LLMError, match="生成摘要失败"):
            provider.summarize("Test Title", "Test Abstract")

    @patch("src.llm_providers.openai_provider.OpenAI")
    def test_summarize_invalid_json(self, mock_openai_class, provider):
        """测试返回无效 JSON."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Invalid JSON"))]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with pytest.raises(LLMError, match="解析 LLM 响应失败"):
            provider.summarize("Test Title", "Test Abstract")

    @patch("src.llm_providers.openai_provider.OpenAI")
    def test_summarize_missing_fields(self, mock_openai_class, provider):
        """测试返回缺少字段的 JSON."""
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps(
                        {
                            "summary": "测试总结",
                            # 缺少其他字段
                        }
                    )
                )
            )
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # 不应该抛出异常，而是使用默认值
        result = provider.summarize("Test Title", "Test Abstract")
        assert result.summary == "测试总结"
        assert result.background == ""  # 默认值

    @patch("src.llm_providers.openai_provider.OpenAI")
    def test_summarize_empty_response(self, mock_openai_class, provider):
        """测试返回空内容."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=None))]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with pytest.raises(LLMError, match="返回空内容"):
            provider.summarize("Test Title", "Test Abstract")

    def test_build_prompt(self, provider):
        """测试 Prompt 构建."""
        prompt = provider._build_prompt("Test Title", "Test Abstract")

        assert "Test Title" in prompt
        assert "Test Abstract" in prompt
        assert "JSON" in prompt
        assert "summary" in prompt

    def test_get_client_without_api_key(self):
        """测试无 API Key 时获取客户端失败."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            provider = OpenAIProvider()
            with pytest.raises(LLMError, match="OPENAI_API_KEY 未配置"):
                provider._get_client()


class TestGeminiProvider:
    """测试 GeminiProvider (预留)."""

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_not_available_without_genai(self):
        """测试未安装 google-generativeai 时不可用."""
        from src.llm_providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()
        assert provider.is_available() is False

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_summarize_not_implemented(self):
        """测试 summarize 方法未实现."""
        from src.llm_providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()

        with pytest.raises(LLMError, match="尚未完全实现"):
            provider.summarize("Test Title", "Test Abstract")

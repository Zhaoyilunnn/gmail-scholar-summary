"""Config 模块测试."""

import os
import tempfile

import pytest

from src.config import Config, GmailConfig, FetcherConfig, LLMConfig, ReportConfig


class TestGmailConfig:
    """测试 GmailConfig."""

    def test_default_values(self):
        """测试默认值."""
        config = GmailConfig()
        assert config.label == "scholar"
        assert config.unread_only is True
        assert config.mark_as_read is True
        assert config.max_emails == 50
        assert config.days_back == 7

    def test_custom_values(self):
        """测试自定义值."""
        config = GmailConfig(
            label="Custom Label",
            unread_only=False,
            mark_as_read=False,
            max_emails=100,
            days_back=14,
        )
        assert config.label == "Custom Label"
        assert config.unread_only is False
        assert config.mark_as_read is False
        assert config.max_emails == 100
        assert config.days_back == 14


class TestFetcherConfig:
    """测试 FetcherConfig."""

    def test_default_values(self):
        """测试默认值."""
        config = FetcherConfig()
        assert config.type == "simple_html"
        assert config.timeout_sec == 30.0
        assert config.retry_times == 3
        assert "Mozilla/5.0" in config.user_agent


class TestLLMConfig:
    """测试 LLMConfig."""

    def test_default_values(self):
        """测试默认值."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000


class TestReportConfig:
    """测试 ReportConfig."""

    def test_default_values(self):
        """测试默认值."""
        config = ReportConfig()
        assert config.format == "markdown"
        assert config.subject_template == "学术周报 - {date}"
        assert config.include_metadata is True
        assert config.min_relevance_score == 6.0


class TestConfigFromYaml:
    """测试从 YAML 加载配置."""

    def test_load_valid_yaml(self):
        """测试加载有效的 YAML 文件."""
        yaml_content = """
gmail:
  label: "Test Label"
  unread_only: false
  max_emails: 20
fetcher:
  type: "docling"
  timeout_sec: 60.0
llm:
  provider: "gemini"
  temperature: 0.5
report:
  format: "html"
  min_relevance_score: 7.0
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.gmail.label == "Test Label"
            assert config.gmail.unread_only is False
            assert config.gmail.max_emails == 20
            assert config.fetcher.type == "docling"
            assert config.fetcher.timeout_sec == 60.0
            assert config.llm.provider == "gemini"
            assert config.llm.temperature == 0.5
            assert config.report.format == "html"
            assert config.report.min_relevance_score == 7.0
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件."""
        with pytest.raises(FileNotFoundError):
            Config.from_yaml("/nonexistent/path/config.yaml")

    def test_load_empty_yaml(self):
        """测试加载空的 YAML 文件."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            # 应该使用默认值
            assert config.gmail.label == "scholar"
            assert config.fetcher.type == "simple_html"
        finally:
            os.unlink(temp_path)


class TestConfigFromEnv:
    """测试从环境变量加载配置."""

    def test_load_from_env(self, monkeypatch):
        """测试从环境变量加载."""
        monkeypatch.setenv("GMAIL_LABEL", "Env Label")
        monkeypatch.setenv("GMAIL_UNREAD_ONLY", "false")
        monkeypatch.setenv("GMAIL_MAX_EMAILS", "25")
        monkeypatch.setenv("FETCHER_TYPE", "docling")
        monkeypatch.setenv("FETCHER_TIMEOUT", "45.0")
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.7")

        config = Config.from_env()
        assert config.gmail.label == "Env Label"
        assert config.gmail.unread_only is False
        assert config.gmail.max_emails == 25
        assert config.fetcher.type == "docling"
        assert config.fetcher.timeout_sec == 45.0
        assert config.llm.provider == "gemini"
        assert config.llm.temperature == 0.7

    def test_default_when_no_env(self, monkeypatch):
        """测试没有环境变量时使用默认值."""
        # 清除所有相关的环境变量
        for key in [
            "GMAIL_LABEL",
            "GMAIL_UNREAD_ONLY",
            "GMAIL_MAX_EMAILS",
            "FETCHER_TYPE",
            "FETCHER_TIMEOUT",
            "LLM_PROVIDER",
            "LLM_TEMPERATURE",
        ]:
            monkeypatch.delenv(key, raising=False)

        config = Config.from_env()
        assert config.gmail.label == "scholar"
        assert config.fetcher.type == "simple_html"
        assert config.llm.provider == "openai"

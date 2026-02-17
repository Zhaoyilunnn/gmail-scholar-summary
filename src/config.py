"""配置管理模块.

提供统一的配置加载和管理功能，支持从 YAML 文件和环境变量读取配置.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

import yaml


@dataclass
class GmailConfig:
    """Gmail 配置."""

    label: str = "scholar"
    unread_only: bool = True
    mark_as_read: bool = True
    max_emails: int = 50
    days_back: int = 7  # 处理最近几天的邮件


@dataclass
class FetcherConfig:
    """Fetcher 配置."""

    type: str = "simple_html"  # simple_html / docling
    timeout_sec: float = 30.0
    retry_times: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class LLMConfig:
    """LLM 配置."""

    provider: str = "openai"  # openai / gemini
    temperature: float = 0.3
    max_tokens: int = 1000


@dataclass
class ReportConfig:
    """报告配置."""

    format: str = "markdown"  # markdown / html
    subject_template: str = "学术周报 - {date}"
    include_metadata: bool = True
    min_relevance_score: float = 6.0


@dataclass
class Config:
    """主配置类."""

    gmail: GmailConfig = field(default_factory=GmailConfig)
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    report: ReportConfig = field(default_factory=ReportConfig)

    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """从 YAML 文件加载配置.

        Args:
            config_path: YAML 配置文件路径.

        Returns:
            Config 实例.

        Raises:
            FileNotFoundError: 配置文件不存在.
            yaml.YAMLError: YAML 解析错误.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置.

        Returns:
            Config 实例.
        """
        config = cls()

        # Gmail 配置
        gmail_label = os.getenv("GMAIL_LABEL")
        if gmail_label:
            config.gmail.label = gmail_label
        gmail_unread_only = os.getenv("GMAIL_UNREAD_ONLY")
        if gmail_unread_only:
            config.gmail.unread_only = gmail_unread_only.lower() == "true"
        gmail_max_emails = os.getenv("GMAIL_MAX_EMAILS")
        if gmail_max_emails:
            config.gmail.max_emails = int(gmail_max_emails)
        gmail_days_back = os.getenv("GMAIL_DAYS_BACK")
        if gmail_days_back:
            config.gmail.days_back = int(gmail_days_back)

        # Fetcher 配置
        fetcher_type = os.getenv("FETCHER_TYPE")
        if fetcher_type:
            config.fetcher.type = fetcher_type
        fetcher_timeout = os.getenv("FETCHER_TIMEOUT")
        if fetcher_timeout:
            config.fetcher.timeout_sec = float(fetcher_timeout)

        # LLM 配置
        llm_provider = os.getenv("LLM_PROVIDER")
        if llm_provider:
            config.llm.provider = llm_provider
        llm_temperature = os.getenv("LLM_TEMPERATURE")
        if llm_temperature:
            config.llm.temperature = float(llm_temperature)

        return config

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置.

        Args:
            data: 配置字典.

        Returns:
            Config 实例.
        """
        gmail_data = data.get("gmail", {})
        fetcher_data = data.get("fetcher", {})
        llm_data = data.get("llm", {})
        report_data = data.get("report", {})

        return cls(
            gmail=GmailConfig(
                label=gmail_data.get("label", "scholar"),
                unread_only=gmail_data.get("unread_only", True),
                mark_as_read=gmail_data.get("mark_as_read", True),
                max_emails=gmail_data.get("max_emails", 50),
                days_back=gmail_data.get("days_back", 7),
            ),
            fetcher=FetcherConfig(
                type=fetcher_data.get("type", "simple_html"),
                timeout_sec=float(fetcher_data.get("timeout_sec", 30.0)),
                retry_times=int(fetcher_data.get("retry_times", 3)),
                user_agent=fetcher_data.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ),
            ),
            llm=LLMConfig(
                provider=llm_data.get("provider", "openai"),
                temperature=float(llm_data.get("temperature", 0.3)),
                max_tokens=int(llm_data.get("max_tokens", 1000)),
            ),
            report=ReportConfig(
                format=report_data.get("format", "markdown"),
                subject_template=report_data.get(
                    "subject_template", "学术周报 - {date}"
                ),
                include_metadata=report_data.get("include_metadata", True),
                min_relevance_score=float(report_data.get("min_relevance_score", 6.0)),
            ),
        )

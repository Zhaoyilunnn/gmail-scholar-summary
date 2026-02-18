"""Gmail Scholar Summary 主程序.

整合所有模块，提供完整的学术周报生成功能.
"""

import argparse
import base64
import logging
import os
import sys
from typing import List

# 加载 .env 文件环境变量
from dotenv import load_dotenv
from src.config import Config
from src.fetchers.simple_html_fetcher import SimpleHTMLFetcher
from src.fetchers.url_processors import process_paper_url
from src.gmail_client import GmailClient, GmailClientError
from src.llm_providers.openai_provider import OpenAIProvider
from src.report_generator import ReportGenerator
from src.summarizer import PaperSummarizer, SummarizerError


load_dotenv()


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False) -> None:
    """设置日志级别.

    Args:
        debug: 是否启用调试模式.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.getLogger().setLevel(level)


def load_config(config_path: str = "config/config.yaml") -> Config:
    """加载配置.

    Args:
        config_path: 配置文件路径.

    Returns:
        Config 实例.
    """
    # 首先尝试从 YAML 加载
    if os.path.exists(config_path):
        logger.info(f"从 {config_path} 加载配置")
        config = Config.from_yaml(config_path)
    else:
        logger.info("配置文件不存在，使用默认配置")
        config = Config()

    # 然后覆盖环境变量
    env_config = Config.from_env()

    # 合并配置（环境变量优先级更高）
    return _merge_configs(config, env_config)


def _merge_configs(base: Config, override: Config) -> Config:
    """合并配置.

    Args:
        base: 基础配置.
        override: 覆盖配置.

    Returns:
        合并后的配置.
    """
    # Gmail 配置
    if override.gmail.label != "Scholar Alerts":
        base.gmail.label = override.gmail.label
    if not override.gmail.unread_only:
        base.gmail.unread_only = override.gmail.unread_only
    if override.gmail.max_emails != 50:
        base.gmail.max_emails = override.gmail.max_emails

    # Fetcher 配置
    if override.fetcher.type != "simple_html":
        base.fetcher.type = override.fetcher.type
    if override.fetcher.timeout_sec != 30.0:
        base.fetcher.timeout_sec = override.fetcher.timeout_sec

    # LLM 配置
    if override.llm.provider != "openai":
        base.llm.provider = override.llm.provider
    if override.llm.temperature != 0.3:
        base.llm.temperature = override.llm.temperature

    return base


def decode_credentials() -> None:
    """从环境变量解码凭证文件.

    GitHub Actions 中凭证以 base64 编码存储在 Secrets 中.
    """
    # 解码 Gmail 凭证
    gmail_creds = os.getenv("GMAIL_CREDENTIALS")
    if gmail_creds:
        logger.debug("解码 Gmail 凭证")
        with open("credentials.json", "w") as f:
            f.write(base64.b64decode(gmail_creds).decode())

    gmail_token = os.getenv("GMAIL_TOKEN")
    if gmail_token:
        logger.debug("解码 Gmail token")
        with open("token.json", "w") as f:
            f.write(base64.b64decode(gmail_token).decode())


def get_unique_links(emails: List[dict]) -> List[str]:
    """从邮件中提取唯一的链接.

    先转换 URL 格式，再基于转换后的 URL 去重，
    避免同一篇论文因不同原始 URL 而被重复处理。

    Args:
        emails: 邮件列表.

    Returns:
        唯一的 URL 列表（已转换格式）.
    """
    seen = set()
    unique_links = []

    for email in emails:
        for link in email.get("links", []):
            # 先转换 URL 格式
            processed_link = process_paper_url(link)
            if processed_link not in seen:
                seen.add(processed_link)
                unique_links.append(processed_link)

    return unique_links


def main() -> int:
    """主函数.

    Returns:
        退出码，0 表示成功.
    """
    parser = argparse.ArgumentParser(
        description="Gmail Scholar Summary - 学术周报生成工具"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，不发送邮件",
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    # 检查代理配置（调试用）
    # httplib2 自动读取 http_proxy/https_proxy 环境变量
    http_proxy = os.getenv("http_proxy") or os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("https_proxy") or os.getenv("HTTPS_PROXY")
    if http_proxy or https_proxy:
        logger.debug(f"代理配置: http_proxy={http_proxy}, https_proxy={https_proxy}")
    else:
        logger.debug("未配置代理，将直接连接")

    try:
        # 1. 加载配置
        logger.info("加载配置...")
        config = load_config(args.config)

        # 2. 解码凭证（GitHub Actions 环境）
        decode_credentials()

        # 3. 初始化 Gmail 客户端
        logger.info("初始化 Gmail 客户端...")
        gmail_client = GmailClient()

        # 4. 获取未读邮件
        logger.info(
            f"获取标签 '{config.gmail.label}' 最近 {config.gmail.days_back} 天的未读邮件..."
        )
        emails = gmail_client.get_unread_scholar_emails(
            label=config.gmail.label,
            max_results=config.gmail.max_emails,
            days_back=config.gmail.days_back,
        )

        if not emails:
            logger.info("没有未读邮件需要处理")
            return 0

        logger.info(f"获取到 {len(emails)} 封邮件")

        # 5. 提取链接
        unique_links = get_unique_links(emails)
        logger.info(f"提取到 {len(unique_links)} 个唯一链接")

        if not unique_links:
            logger.warning("邮件中没有找到论文链接")
            return 0

        # 6. 初始化 Summarizer
        logger.info("初始化论文摘要器...")
        summarizer = PaperSummarizer(
            fetcher=SimpleHTMLFetcher(
                timeout_sec=config.fetcher.timeout_sec,
                retry_times=config.fetcher.retry_times,
            ),
            llm_provider=OpenAIProvider(),
        )

        # 7. 处理论文
        logger.info("开始处理论文...")
        papers = summarizer.process_urls(unique_links)

        if not papers:
            logger.warning("没有成功处理任何论文")
            return 0

        logger.info(f"成功处理 {len(papers)} 篇论文")

        # 8. 生成报告
        logger.info("生成周报...")
        generator = ReportGenerator(config.report)

        if config.report.format == "html":
            report = generator.generate_html(papers)
            is_html = True
        else:
            report = generator.generate_markdown(papers)
            is_html = False

        # 9. 发送邮件（如果不是 dry-run）
        if not args.dry_run:
            recipient = os.getenv("RECIPIENT_EMAIL")
            if not recipient:
                logger.error("RECIPIENT_EMAIL 未设置")
                return 1

            from datetime import datetime

            date_str = datetime.now().strftime("%Y-%m-%d")
            subject = config.report.subject_template.format(date=date_str)

            logger.info(f"发送邮件到 {recipient}...")
            gmail_client.send_email(
                to=recipient,
                subject=subject,
                body=report,
                html=is_html,
            )

            # 10. 标记邮件为已读
            if config.gmail.mark_as_read:
                logger.info("标记邮件为已读...")
                message_ids = [email["id"] for email in emails]
                gmail_client.batch_mark_as_read(message_ids)

            logger.info("周报发送成功！")
        else:
            # 试运行模式，打印报告
            print("\n" + "=" * 80)
            print("试运行模式 - 报告预览：")
            print("=" * 80)
            print(report)
            print("=" * 80)

        return 0

    except GmailClientError as e:
        logger.error(f"Gmail 客户端错误: {e}")
        return 1
    except SummarizerError as e:
        logger.error(f"摘要器错误: {e}")
        return 1
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

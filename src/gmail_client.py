"""Gmail API 客户端模块.

提供 Gmail 邮件的读取、发送和管理功能.
"""

import base64
import logging
import os
import re
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailClientError(Exception):
    """Gmail 客户端错误."""

    pass


class GmailClient:
    """Gmail API 客户端.

    提供邮件读取、发送、标记等功能.

    Attributes:
        service: Gmail API 服务对象.
        user_id: 用户 ID，默认为 'me'.

    Note:
        代理设置: 本客户端会自动读取 http_proxy/https_proxy 环境变量.
        在 .env 文件中配置: http_proxy=http://127.0.0.1:7890
    """

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ):
        """初始化 Gmail 客户端.

        Args:
            credentials_path: OAuth2 凭证文件路径.
            token_path: Token 文件路径.

        Raises:
            GmailClientError: 认证失败.
        """
        self.user_id = "me"
        self.service = self._authenticate(credentials_path, token_path)

    def _authenticate(self, credentials_path: str, token_path: str) -> Any:
        """认证并创建 Gmail 服务.

        Args:
            credentials_path: OAuth2 凭证文件路径.
            token_path: Token 文件路径.

        Returns:
            Gmail API 服务对象.

        Raises:
            GmailClientError: 认证失败.
        """
        creds = None

        # 加载已有的 token
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        # 如果没有有效凭证，需要重新认证
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    raise GmailClientError(f"凭证文件不存在: {credentials_path}")
                from google_auth_oauthlib.flow import InstalledAppFlow

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # 保存 token
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        try:
            # httplib2 会自动读取 http_proxy/https_proxy 环境变量
            # 无需显式配置代理
            logger.info("正在连接 Gmail API...")
            service = build("gmail", "v1", credentials=creds)
            logger.info("✅ 成功创建 Gmail 服务")
            return service
        except Exception as e:
            logger.error(f"❌ 连接 Gmail API 失败: {e}")
            raise GmailClientError(f"创建 Gmail 服务失败: {e}")

    def get_unread_scholar_emails(
        self,
        label: str = "scholar",
        max_results: int = 50,
        days_back: int = 7,
    ) -> List[Dict]:
        """获取指定标签下最近一段时间的未读邮件.

        Args:
            label: 标签名称.
            max_results: 最大返回邮件数.
            days_back: 处理最近几天的邮件（默认最近一周）.

        Returns:
            邮件列表，每个邮件包含 id, subject, snippet, links 等.

        Raises:
            GmailClientError: API 调用失败.
        """
        try:
            # 构建搜索查询
            # 计算日期范围
            if days_back > 0:
                # Gmail 查询语法: after:YYYY/MM/DD
                # 使用内部日期（邮件接收时间）
                date_since = (datetime.now() - timedelta(days=days_back)).strftime(
                    "%Y/%m/%d"
                )
                query = f"label:{label} is:unread after:{date_since}"
            else:
                query = f"label:{label} is:unread"

            logger.debug(f"搜索查询: {query}")

            results = (
                self.service.users()
                .messages()
                .list(userId=self.user_id, q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                email = self._get_email_details(msg["id"])
                if email:
                    emails.append(email)

            logger.info(
                f"获取到 {len(emails)} 封未读邮件（标签: {label}, 最近 {days_back} 天）"
            )
            return emails

        except HttpError as e:
            raise GmailClientError(f"获取邮件失败: {e}")

    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """获取邮件详细信息.

        Args:
            message_id: 邮件 ID.

        Returns:
            邮件详情字典，失败返回 None.
        """
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId=self.user_id, id=message_id)
                .execute()
            )

            headers = msg["payload"]["headers"]
            subject = ""
            sender = ""

            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]

            # 提取正文
            body = self._extract_body(msg["payload"])

            # 提取链接
            links = self._extract_links(body)

            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "snippet": msg.get("snippet", ""),
                "body": body,
                "links": links,
                "internalDate": msg.get("internalDate"),
            }

        except Exception as e:
            logger.error(f"获取邮件详情失败 {message_id}: {e}")
            return None

    def _extract_body(self, payload: Dict) -> str:
        """从 payload 提取邮件正文.

        Args:
            payload: 邮件 payload.

        Returns:
            邮件正文文本.
        """
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body += base64.urlsafe_b64decode(data).decode("utf-8")
                elif part["mimeType"] == "text/html":
                    data = part["body"].get("data", "")
                    if data:
                        html = base64.urlsafe_b64decode(data).decode("utf-8")
                        # 简单去除 HTML 标签
                        body += re.sub(r"<[^>]+>", " ", html)
        else:
            data = payload["body"].get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        return body

    def _extract_links(self, text: str) -> List[str]:
        """从文本中提取 URL 链接.

        Args:
            text: 文本内容.

        Returns:
            URL 列表.
        """
        # 匹配 URL 的正则表达式
        url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
        urls = re.findall(url_pattern, text)

        # 过滤和清理
        cleaned_urls = []
        for url in urls:
            # 去除末尾的标点
            url = url.rstrip(".,;:!?)")
            # 只保留 scholar.google.com 和 arxiv.org 的链接
            if "scholar.google.com" in url or "arxiv.org" in url:
                cleaned_urls.append(url)

        return cleaned_urls

    def send_email(self, to: str, subject: str, body: str, html: bool = True) -> str:
        """发送邮件.

        Args:
            to: 收件人邮箱.
            subject: 邮件主题.
            body: 邮件内容.
            html: 是否为 HTML 格式.

        Returns:
            邮件 ID.

        Raises:
            GmailClientError: 发送失败.
        """
        try:
            message = MIMEMultipart()
            message["to"] = to
            message["subject"] = subject

            if html:
                msg_body = MIMEText(body, "html", "utf-8")
            else:
                msg_body = MIMEText(body, "plain", "utf-8")

            message.attach(msg_body)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            result = (
                self.service.users()
                .messages()
                .send(userId=self.user_id, body={"raw": raw_message})
                .execute()
            )

            logger.info(f"邮件发送成功: {result['id']}")
            return result["id"]

        except HttpError as e:
            raise GmailClientError(f"发送邮件失败: {e}")

    def mark_as_read(self, message_id: str) -> None:
        """标记邮件为已读.

        Args:
            message_id: 邮件 ID.

        Raises:
            GmailClientError: 操作失败.
        """
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()

            logger.debug(f"邮件标记为已读: {message_id}")

        except HttpError as e:
            raise GmailClientError(f"标记邮件失败: {e}")

    def batch_mark_as_read(self, message_ids: List[str]) -> None:
        """批量标记邮件为已读.

        Args:
            message_ids: 邮件 ID 列表.
        """
        for msg_id in message_ids:
            try:
                self.mark_as_read(msg_id)
            except GmailClientError as e:
                logger.error(f"批量标记失败 {msg_id}: {e}")

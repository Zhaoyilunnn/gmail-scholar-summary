"""Gmail Client 模块测试."""

import base64
from unittest.mock import Mock, patch

import pytest

from src.gmail_client import GmailClient, GmailClientError


class TestGmailClient:
    """测试 GmailClient."""

    @patch("src.gmail_client.build")
    @patch("src.gmail_client.os.path.exists")
    @patch("src.gmail_client.Credentials")
    def test_init_with_valid_token(self, mock_creds, mock_exists, mock_build):
        """测试使用有效 token 初始化."""
        mock_exists.return_value = True
        mock_creds.from_authorized_user_file.return_value = Mock(valid=True)
        mock_build.return_value = Mock()

        client = GmailClient()

        assert client.user_id == "me"
        assert client.service is not None

    @patch("src.gmail_client.build")
    @patch("src.gmail_client.os.path.exists")
    @patch("src.gmail_client.Credentials")
    def test_init_missing_credentials(self, mock_creds, mock_exists, mock_build):
        """测试缺少凭证文件."""
        mock_exists.return_value = False
        mock_creds.from_authorized_user_file.return_value = None

        with pytest.raises(GmailClientError):
            GmailClient()


class TestGetUnreadEmails:
    """测试获取未读邮件功能."""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的 GmailClient."""
        with patch.object(GmailClient, "_authenticate") as mock_auth:
            mock_auth.return_value = Mock()
            client = GmailClient.__new__(GmailClient)
            client.user_id = "me"
            client.service = Mock()
            return client

    def test_get_unread_scholar_emails_success(self, mock_client):
        """测试成功获取未读邮件."""
        # 模拟邮件列表
        mock_client.service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}]
        }

        # 模拟邮件详情
        mock_client.service.users().messages().get().execute.side_effect = [
            {
                "id": "msg1",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test Subject 1"},
                        {"name": "From", "value": "scholar@google.com"},
                    ],
                    "body": {"data": base64.urlsafe_b64encode(b"Test body 1").decode()},
                },
                "snippet": "Snippet 1",
                "internalDate": "1234567890",
            },
            {
                "id": "msg2",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test Subject 2"},
                        {"name": "From", "value": "scholar@google.com"},
                    ],
                    "body": {"data": base64.urlsafe_b64encode(b"Test body 2").decode()},
                },
                "snippet": "Snippet 2",
                "internalDate": "1234567891",
            },
        ]

        emails = mock_client.get_unread_scholar_emails("Scholar Alerts")

        assert len(emails) == 2
        assert emails[0]["id"] == "msg1"
        assert emails[0]["subject"] == "Test Subject 1"

    def test_get_unread_scholar_emails_empty(self, mock_client):
        """测试没有未读邮件."""
        mock_client.service.users().messages().list().execute.return_value = {
            "messages": []
        }

        emails = mock_client.get_unread_scholar_emails("Scholar Alerts")

        assert emails == []

    def test_get_unread_scholar_emails_api_error(self, mock_client):
        """测试 API 调用失败."""
        from googleapiclient.errors import HttpError

        mock_client.service.users().messages().list().execute.side_effect = HttpError(
            Mock(status=500), b"Internal Error"
        )

        with pytest.raises(GmailClientError):
            mock_client.get_unread_scholar_emails("Scholar Alerts")

    def test_get_unread_scholar_emails_with_days_back(self, mock_client):
        """测试使用 days_back 参数筛选邮件."""
        mock_client.service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1"}]
        }

        mock_client.service.users().messages().get().execute.return_value = {
            "id": "msg1",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "scholar@google.com"},
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Test body").decode()},
            },
            "snippet": "Snippet",
            "internalDate": "1234567890",
        }

        # 测试 days_back=7
        emails = mock_client.get_unread_scholar_emails(label="scholar", days_back=7)

        assert len(emails) == 1
        # 验证查询中包含 after: 日期
        call_args = mock_client.service.users().messages().list.call_args
        assert "after:" in call_args[1]["q"]

    def test_get_unread_scholar_emails_default_days_back(self, mock_client):
        """测试默认使用 scholar 标签."""
        mock_client.service.users().messages().list().execute.return_value = {
            "messages": []
        }

        mock_client.get_unread_scholar_emails()

        # 验证默认使用 scholar 标签
        call_args = mock_client.service.users().messages().list.call_args
        assert "label:scholar" in call_args[1]["q"]


class TestExtractLinks:
    """测试链接提取功能."""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的 GmailClient."""
        client = GmailClient.__new__(GmailClient)
        return client

    def test_extract_scholar_links(self, mock_client):
        """测试提取 Google Scholar 链接."""
        text = """
        Check out this paper: https://scholar.google.com/scholar?cluster=123
        Another one: https://scholar.google.com/scholar?cluster=456
        """

        links = mock_client._extract_links(text)

        assert len(links) == 2
        assert "scholar.google.com" in links[0]

    def test_extract_arxiv_links(self, mock_client):
        """测试提取 arXiv 链接."""
        text = """
        Paper: https://arxiv.org/abs/2401.12345
        PDF: https://arxiv.org/pdf/2401.12345.pdf
        """

        links = mock_client._extract_links(text)

        assert len(links) == 2
        assert "arxiv.org" in links[0]

    def test_extract_no_matching_links(self, mock_client):
        """测试没有匹配链接的情况."""
        text = "Check out https://example.com/paper and http://test.com/doc"

        links = mock_client._extract_links(text)

        assert links == []


class TestSendEmail:
    """测试发送邮件功能."""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的 GmailClient."""
        client = GmailClient.__new__(GmailClient)
        client.user_id = "me"
        client.service = Mock()
        return client

    def test_send_email_html_success(self, mock_client):
        """测试成功发送 HTML 邮件."""
        mock_client.service.users().messages().send().execute.return_value = {
            "id": "sent_msg_123"
        }

        msg_id = mock_client.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="<h1>Test</h1>",
            html=True,
        )

        assert msg_id == "sent_msg_123"

    def test_send_email_plain_text(self, mock_client):
        """测试发送纯文本邮件."""
        mock_client.service.users().messages().send().execute.return_value = {
            "id": "sent_msg_456"
        }

        msg_id = mock_client.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Plain text content",
            html=False,
        )

        assert msg_id == "sent_msg_456"

    def test_send_email_failure(self, mock_client):
        """测试发送邮件失败."""
        from googleapiclient.errors import HttpError

        mock_client.service.users().messages().send().execute.side_effect = HttpError(
            Mock(status=403), b"Forbidden"
        )

        with pytest.raises(GmailClientError):
            mock_client.send_email(
                to="test@example.com",
                subject="Test",
                body="Content",
            )


class TestMarkAsRead:
    """测试标记已读功能."""

    @pytest.fixture
    def mock_client(self):
        """创建模拟的 GmailClient."""
        client = GmailClient.__new__(GmailClient)
        client.user_id = "me"
        client.service = Mock()
        return client

    def test_mark_as_read_success(self, mock_client):
        """测试成功标记为已读."""
        mock_client.service.users().messages().modify().execute.return_value = {}

        # 不应该抛出异常
        mock_client.mark_as_read("msg_123")

    def test_mark_as_read_failure(self, mock_client):
        """测试标记失败."""
        from googleapiclient.errors import HttpError

        mock_client.service.users().messages().modify().execute.side_effect = HttpError(
            Mock(status=404), b"Not Found"
        )

        with pytest.raises(GmailClientError):
            mock_client.mark_as_read("msg_123")

    def test_batch_mark_as_read(self, mock_client):
        """测试批量标记已读."""
        mock_client.service.users().messages().modify().execute.return_value = {}
        mock_client.service.reset_mock()

        mock_client.batch_mark_as_read(["msg1", "msg2", "msg3"])

        assert mock_client.service.users().messages().modify.call_count == 3

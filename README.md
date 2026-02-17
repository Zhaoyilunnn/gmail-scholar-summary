# Gmail Scholar Summary

自动从 Gmail 中获取 Google Scholar 论文通知邮件，使用 LLM 生成中文摘要，并发送周报报告。

## 功能特性

- 📧 **自动读取 Gmail**: 从指定标签获取未读邮件
- 🔍 **智能解析**: 自动提取论文链接并获取信息
- 🤖 **AI 摘要**: 使用 OpenAI API 生成中文摘要
- 📊 **周报生成**: 生成 Markdown/HTML 格式报告
- 🚀 **GitHub Actions**: 每周自动运行

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/gmail-scholar-summary.git
cd gmail-scholar-summary
```

### 2. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 4. 运行

```bash
# 本地运行（试运行模式，不发送邮件）
uv run python src/main.py --dry-run

# 生产运行
uv run python src/main.py
```

## GitHub Actions 部署

### 1. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加以下 Secrets:

| Secret Name | Required | Description |
|-------------|----------|-------------|
| `GMAIL_CREDENTIALS` | ✅ | Base64 编码的 Gmail API 凭证 |
| `GMAIL_TOKEN` | ✅ | Base64 编码的 OAuth token |
| `RECIPIENT_EMAIL` | ✅ | 报告接收邮箱 |
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 |
| `OPENAI_BASE_URL` | ⚠️ | API Base URL（默认 https://api.openai.com/v1）|
| `OPENAI_MODEL` | ⚠️ | 模型名称（默认 gpt-4o-mini）|

### 2. 生成 Gmail 凭证

```bash
# 1. 从 Google Cloud Console 下载 credentials.json

# 2. 本地运行获取 token
uv run python -c "from src.gmail_client import GmailClient; GmailClient()"

# 3. 编码为 base64
cat credentials.json | base64
cat token.json | base64
```

### 3. 手动触发

在 GitHub 仓库页面 → Actions → Weekly Scholar Summary → Run workflow

## 配置说明

### 配置文件 (config/config.yaml)

```yaml
gmail:
  label: "Scholar Alerts"      # 监控的标签
  unread_only: true            # 只处理未读邮件
  mark_as_read: true          # 处理后标记为已读
  max_emails: 50              # 每次最多处理邮件数

fetcher:
  type: "simple_html"         # simple_html / docling
  timeout_sec: 30             # 请求超时时间
  retry_times: 3              # 重试次数

llm:
  provider: "openai"          # openai / gemini
  temperature: 0.3           # 温度参数
  max_tokens: 1000           # 最大 token 数

report:
  format: "markdown"          # markdown / html
  subject_template: "学术周报 - {date}"
```

## 开发

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_gmail_client.py

# 运行单个测试函数
uv run pytest tests/test_gmail_client.py -k "test_get_unread_emails"
```

### 代码检查

```bash
# Lint 检查
uv run ruff check src/ tests/

# 代码格式化
uv run ruff format src/ tests/
```

## 架构设计

```
gmail-scholar-summary/
├── src/
│   ├── fetchers/              # 论文获取（可扩展）
│   │   ├── base.py
│   │   ├── simple_html_fetcher.py
│   │   └── docling_fetcher.py  # 预留
│   ├── llm_providers/         # LLM Provider（可扩展）
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   └── gemini_provider.py  # 预留
│   ├── gmail_client.py
│   ├── summarizer.py
│   ├── report_generator.py
│   └── main.py
├── tests/
├── config/
├── .github/workflows/
└── README.md
```

## License

MIT License

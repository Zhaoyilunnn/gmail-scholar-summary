# Gmail Scholar Summary

自动从 Gmail 中获取 Google Scholar 论文通知邮件，使用 LLM 生成中文摘要，并发送周报报告。

## 使用场景 / Motivation

在 Google Scholar 为多位研究者订阅了新论文提醒，这些通知通过 Gmail 统一归档到 Scholar 标签。由于没有时间逐一打开阅读，收件箱很快被新论文邮件淹没，难以及时判断哪些论文值得进入自己的文献库。

这个工具会每周自动从这些邮件中提取论文链接、抓取基础信息，并用中文生成结构化摘要（一句话总结、研究背景、核心方法、主要结果），最终输出 Markdown/HTML 周报，帮助快速筛选与保存，减少收件箱负担、提升文献跟踪效率。

## 功能特性

- 📧 **自动读取 Gmail**: 从指定标签获取未读邮件
- 🔍 **智能解析**: 自动提取论文链接并获取信息
- 🤖 **AI 摘要**: 使用 OpenAI API 生成中文摘要
- 📊 **周报生成**: 生成 Markdown/HTML 格式报告
- 🚀 **GitHub Actions**: 每周自动运行

## 快速开始

### 1. Fork 并克隆仓库

```bash
# 先在 GitHub 上 Fork 本仓库到你的账号
# 然后克隆你的 Fork 到本地
git clone https://github.com/<your-account>/gmail-scholar-summary.git
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

<details> <summary>点击展开详细步骤</summary>

#### 步骤 1: 创建 Google Cloud 项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击顶部项目下拉菜单 → **新建项目**
3. 输入项目名称（如 `gmail-scholar-summary`）→ **创建**

#### 步骤 2: 启用 Gmail API

1. 在新项目中，点击左上角菜单 → **API 和服务** → **库**
2. 搜索 **Gmail API** → 点击进入 → **启用**

#### 步骤 3: 配置 OAuth 同意屏幕

1. 左侧菜单 → **API 和服务** → **OAuth 同意屏幕**
2. 选择 **外部**（适用于任何 Google 账号）→ **创建**
3. 填写应用信息：
   - **应用名称**: Gmail Scholar Summary
   - **用户支持邮箱**: 你的邮箱
   - **开发者联系邮箱**: 你的邮箱
4. 点击 **保存并继续** → **保存并继续**（无需添加测试用户）
5. 点击 **返回信息中心**

#### 步骤 4: 创建 OAuth2 凭证

1. 左侧菜单 → **凭据** → **创建凭据** → **OAuth 客户端 ID**
2. **应用类型**: 选择 **桌面应用**
3. **名称**: Gmail Scholar Summary Client
4. 点击 **创建**
5. 弹出窗口显示 **客户端 ID** 和 **客户端密钥** → 点击 **下载 JSON**
6. 将下载的文件重命名为 `credentials.json`

#### 步骤 5: 生成本地授权 Token

```bash
# 将 credentials.json 放到项目根目录
mv ~/Downloads/client_secret_*.json credentials.json

# 运行授权脚本
uv run python -c "from src.gmail_client import GmailClient; c = GmailClient()"

# 这会打开浏览器让你授权，授权后会生成 token.json
```

#### 步骤 6: 编码为 base64 添加到 GitHub Secrets

```bash
# macOS/Linux
cat credentials.json | base64 | pbcopy  # 复制到剪贴板
cat token.json | base64 | pbcopy        # 复制到剪贴板

# 或在终端直接显示（然后复制）
cat credentials.json | base64
cat token.json | base64
```

将这两个 base64 字符串分别添加到 GitHub Secrets:
- `GMAIL_CREDENTIALS`: credentials.json 的 base64
- `GMAIL_TOKEN`: token.json 的 base64

**注意**: token.json 包含 refresh token，有效期较长。如果授权过期，需要重新生成本地 token 并更新 Secret。


</details>

### 3. 手动触发

在 GitHub 仓库页面 → Actions → Weekly Scholar Summary → Run workflow

## 配置说明

### 配置文件 (config/config.yaml)

```yaml
gmail:
  label: "scholar"      # 监控的标签
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
uv run pytest tests/test_gmail_client.py -k "test_extract_scholar_url_links"
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
│   │   ├── url_processors.py  # URL 处理器（Google Scholar → arXiv）
│   │   └── docling_fetcher.py  # 预留
│   ├── llm_providers/         # LLM Provider（可扩展）
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   └── gemini_provider.py  # 预留
│   ├── link_filters.py        # 链接过滤器（筛选论文链接）
│   ├── config.py              # 配置管理
│   ├── gmail_client.py
│   ├── summarizer.py
│   └── report_generator.py
├── main.py                    # 主入口（项目根目录）
├── tests/
├── config/
├── .github/workflows/
└── README.md
```

## 未来功能 (TODO)

- [ ] **基于研究兴趣的相关度评分**：支持配置个人研究兴趣，LLM 自动判断论文与兴趣的匹配度并输出评分

## License

Apache License 2.0

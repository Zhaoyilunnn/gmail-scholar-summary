# Gmail 学术新论文自动摘要与周报报告工具 - 开发计划

**部署方式**: GitHub Actions  
**技术栈**: Python 3.11+ + Gmail API + OpenAI API

---

## 一、项目架构

```
gmail-scholar-summary/
│
├── .github/
│   └── workflows/
│       └── weekly-summary.yml    # GitHub Actions 工作流
│
├── src/
│   ├── __init__.py
│   ├── config.py                 # 配置管理
│   ├── gmail_client.py           # Gmail API 客户端
│   ├── fetchers/                 # 论文信息获取（可扩展）
│   │   ├── __init__.py
│   │   ├── base.py               # Fetcher 抽象基类
│   │   ├── simple_html_fetcher.py # 默认：简单 HTML 解析
│   │   └── docling_fetcher.py    # 扩展：Docling 解析（预留）
│   ├── llm_providers/            # LLM Provider（可扩展）
│   │   ├── __init__.py
│   │   ├── base.py               # Provider 抽象基类
│   │   ├── openai_provider.py    # OpenAI 兼容接口
│   │   └── gemini_provider.py    # Gemini 接口（预留）
│   ├── summarizer.py             # LLM 摘要生成
│   ├── report_generator.py       # 报告生成
│   └── main.py                   # 主入口
│
├── config/
│   └── config.yaml               # 配置文件模板
│
├── tests/
│   ├── test_gmail_client.py
│   ├── test_paper_fetcher.py
│   └── test_summarizer.py
│
├── requirements.txt              # Python 依赖
├── README.md                     # 项目说明
├── .env.example                  # 环境变量示例
└── .gitignore
```

---

## 二、开发阶段

### 阶段 1: 基础架构搭建

**任务列表**:
- [ ] 创建项目目录结构（含 fetchers/ 和 llm_providers/ 子包）
- [ ] 初始化 Git 仓库
- [ ] 编写 `requirements.txt`
- [ ] 配置 GitHub Actions 基础工作流

**关键文件**:
- `requirements.txt` - Python 依赖
- `.github/workflows/weekly-summary.yml` - GitHub Actions 工作流

---

### 阶段 2: Gmail 集成

**任务列表**:
- [ ] 创建 Gmail API 项目并获取凭证
- [ ] 实现 Gmail 客户端类
- [ ] 实现邮件搜索与读取功能
- [ ] 实现邮件标记已读功能
- [ ] 实现邮件发送功能

**核心代码**:
- `src/gmail_client.py` - Gmail API 封装
  - `get_unread_scholar_emails(label)` - 获取指定标签下的未读邮件
  - `extract_paper_links(email)` - 从邮件中提取论文链接
  - `send_email(to, subject, body)` - 发送邮件
  - `mark_as_read(message_id)` - 标记邮件为已读

---

### 阶段 3: 论文信息获取（可扩展架构）

**设计原则**: 默认使用最简单的 HTML 解析，但架构上支持无缝扩展其他工具（如 docling）

**任务列表**:
- [ ] 设计 Fetcher 抽象基类
- [ ] 实现默认的 SimpleHTMLFetcher（使用 BeautifulSoup）
- [ ] 支持 Google Scholar 页面解析
- [ ] 支持 arXiv 页面解析
- [ ] 添加重试机制和错误处理
- [ ] 通过配置切换不同 Fetcher

**核心代码**:
- `src/fetchers/base.py` - 抽象基类

```python
from abc import ABC, abstractmethod
from typing import Dict

class PaperFetcher(ABC):
    """论文信息获取器抽象基类."""
    
    @abstractmethod
    def fetch(self, url: str) -> Dict:
        """从 URL 获取论文信息.
        
        Returns:
            {
                'title': str,
                'authors': List[str],
                'abstract': str,
                'url': str
            }
        """
        pass
```

- `src/fetchers/simple_html_fetcher.py` - 默认实现

```python
class SimpleHTMLFetcher(PaperFetcher):
    """基于 BeautifulSoup 的简单 HTML 解析器."""
    
    def __init__(self, timeout_sec: float = 30.0):
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
    
    def fetch(self, url: str) -> Dict:
        """获取论文信息."""
        response = self.session.get(url, timeout=self.timeout_sec)
        response.raise_for_status()
        return self._parse_html(response.text, url)
    
    def _parse_html(self, html: str, url: str) -> Dict:
        """解析 HTML 提取论文信息."""
        # 使用 BeautifulSoup 解析
        # 支持 Google Scholar 和 arXiv 页面
        pass
```

- `src/fetchers/docling_fetcher.py` - 扩展实现（预留接口）

```python
class DoclingFetcher(PaperFetcher):
    """基于 Docling 的高级文档解析器.
    
    安装: pip install docling
    优势: 更好的 PDF 和复杂页面解析能力
    """
    
    def __init__(self):
        # 预留 docling 集成接口
        pass
```

**配置方式**:
```yaml
# config.yaml
fetcher:
  type: "simple_html"           # simple_html / docling / arxiv_api
  timeout_sec: 30
  retry_times: 3
```

---

### 阶段 4: LLM 摘要生成（多 Provider 架构）

**设计原则**: 通过 GitHub Secrets 配置 LLM 参数，支持 OpenAI 兼容接口和 Gemini

**任务列表**:
- [ ] 设计 LLM Provider 抽象基类
- [ ] 实现 OpenAIProvider（支持自定义 base_url）
- [ ] 预留 GeminiProvider 接口
- [ ] 通过 GitHub Secrets 配置 API 参数
- [ ] 设计中文摘要 Prompt
- [ ] 实现批处理和错误处理

**GitHub Secrets 配置**:
```yaml
# 必需 Secrets
OPENAI_API_KEY: "sk-..."                    # OpenAI API 密钥
OPENAI_BASE_URL: "https://api.openai.com/v1" # 支持自定义 base URL（如 OpenRouter）
OPENAI_MODEL: "gpt-4o-mini"                  # 模型名称

# 可选 Secrets（后续支持）
GEMINI_API_KEY: ""                           # Gemini API 密钥（预留）
```

**核心代码**:
- `src/llm_providers/base.py` - 抽象基类

```python
from abc import ABC, abstractmethod
from typing import Dict

class LLMProvider(ABC):
    """LLM Provider 抽象基类."""
    
    @abstractmethod
    def summarize(self, title: str, abstract: str) -> Dict:
        """生成论文中文摘要.
        
        Returns:
            {
                'summary': str,           # 一句话总结
                'background': str,        # 研究背景
                'method': str,           # 核心方法
                'results': str,          # 主要结果
                'relevance_score': float # 相关度评分 1-10
            }
        """
        pass
```

- `src/llm_providers/openai_provider.py` - OpenAI 实现

```python
import os
from openai import OpenAI

class OpenAIProvider(LLMProvider):
    """OpenAI 兼容接口 Provider.
    
    支持标准 OpenAI API 和兼容接口（如 OpenRouter、中转站等）
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def summarize(self, title: str, abstract: str) -> Dict:
        """生成论文摘要."""
        prompt = self._build_prompt(title, abstract)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位学术研究助手..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return self._parse_response(response)
```

- `src/llm_providers/gemini_provider.py` - Gemini 实现（预留）

```python
class GeminiProvider(LLMProvider):
    """Google Gemini Provider.
    
    使用 GEMINI_API_KEY 环境变量
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 预留 Gemini 集成
        pass
```

**Prompt 模板**:
```
你是一位学术研究助手。请对以下学术论文进行中文总结。

论文标题: {title}
论文摘要: {abstract}

请按以下 JSON 格式输出:
{
    "summary": "一句话总结",
    "background": "研究背景",
    "method": "核心方法",
    "results": "主要结果",
    "relevance_score": 8.5
}

要求:
1. summary 控制在 50 字以内
2. background、method、results 每部分 100 字以内
3. relevance_score 为 1-10 的浮点数
4. 只输出 JSON，不要其他内容
```

**配置方式**:
```yaml
# config.yaml
llm:
  provider: "openai"              # openai / gemini
  temperature: 0.3
  max_tokens: 1000
```

---

### 阶段 5: 报告生成与邮件发送

**任务列表**:
- [ ] 实现 Markdown 报告生成
- [ ] 实现 HTML 报告生成（可选）
- [ ] 设计报告模板
- [ ] 集成邮件发送功能

**核心代码**:
- `src/report_generator.py` - 报告生成器
  - `generate_markdown(papers)` - 生成 Markdown 报告
  - `generate_html(papers)` - 生成 HTML 报告

**报告模板**:
```markdown
# 学术周报 - {date}

本周共处理 {count} 篇论文

## 论文列表

### 1. {论文标题}
**作者**: {authors}

📋 一句话总结: ...
🔍 研究背景: ...
💡 核心方法: ...
📊 主要结果: ...
⭐ 相关度评分: {score}/10
```

---

### 阶段 6: GitHub Actions 部署配置

**任务列表**:
- [ ] 完善 GitHub Actions 工作流
- [ ] 配置 GitHub Secrets（含 LLM 配置）
- [ ] 添加运行日志和通知
- [ ] 测试手动触发和定时触发

**GitHub Actions 工作流**:
```yaml
name: Weekly Scholar Summary

on:
  schedule:
    - cron: '0 1 * * 1'  # 每周一上午 9:00 (UTC+8)
  workflow_dispatch:      # 支持手动触发

jobs:
  summarize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install -r requirements.txt
      
      - name: Decode credentials
        run: |
          echo "${{ secrets.GMAIL_CREDENTIALS }}" | base64 -d > credentials.json
          echo "${{ secrets.GMAIL_TOKEN }}" | base64 -d > token.json
      
      - name: Run summarizer
        env:
          # Gmail 配置
          GMAIL_CREDENTIALS: ${{ secrets.GMAIL_CREDENTIALS }}
          GMAIL_TOKEN: ${{ secrets.GMAIL_TOKEN }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
          # LLM 配置（必需）
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}
          OPENAI_MODEL: ${{ secrets.OPENAI_MODEL }}
          # LLM 配置（可选，预留）
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python src/main.py
```

**GitHub Secrets 配置**:

| Secret Name | Required | Description |
|-------------|----------|-------------|
| `GMAIL_CREDENTIALS` | ✅ | Base64 编码的 Gmail API 凭证 |
| `GMAIL_TOKEN` | ✅ | Base64 编码的 OAuth token |
| `RECIPIENT_EMAIL` | ✅ | 报告接收邮箱地址 |
| `OPENAI_API_KEY` | ✅ | OpenAI API 密钥 |
| `OPENAI_BASE_URL` | ⚠️ | OpenAI API Base URL（默认 https://api.openai.com/v1）|
| `OPENAI_MODEL` | ⚠️ | 模型名称（默认 gpt-4o-mini）|
| `GEMINI_API_KEY` | ❌ | Gemini API 密钥（预留）|

---

### 阶段 7: 测试与优化

**任务列表**:
- [ ] 编写完整单元测试套件
- [ ] 进行集成测试
- [ ] 添加错误处理和日志记录
- [ ] 性能优化（批量处理、缓存）

**测试策略**:
- 单元测试: `tests/test_*.py`
- 集成测试: 端到端流程测试
- Mock: Gmail API、HTTP 请求、LLM API

---

## 三、配置文件

### config/config.yaml

```yaml
# Gmail 配置
gmail:
  label: "Scholar Alerts"           # 监控的标签
  unread_only: true                 # 只处理未读邮件
  mark_as_read: true               # 处理后标记为已读
  max_emails: 50                   # 每次最多处理邮件数

# Fetcher 配置
fetcher:
  type: "simple_html"              # simple_html / docling / arxiv_api
  timeout_sec: 30                  # 请求超时时间
  retry_times: 3                   # 重试次数
  user_agent: "Mozilla/5.0..."     # 自定义 User-Agent

# LLM 配置
llm:
  provider: "openai"               # openai / gemini
  temperature: 0.3                # 温度参数
  max_tokens: 1000                # 最大 token 数

# 报告配置
report:
  format: "markdown"              # markdown / html
  subject_template: "学术周报 - {date}"
  include_metadata: true          # 包含论文元数据
  min_relevance_score: 6.0        # 最低相关度阈值
```

---

## 四、运行流程

```
Gmail (Scholar Alerts)
    ↓
[1] 获取未读邮件 (Gmail API)
    ↓
[2] 提取论文链接
    ↓
[3] 爬取论文信息 (Fetcher: SimpleHTMLFetcher / DoclingFetcher)
    ↓
[4] LLM 中文总结 (Provider: OpenAIProvider / GeminiProvider)
    ↓
[5] 生成周报 (Markdown/HTML)
    ↓
[6] 发送邮件 (Gmail API)
    ↓
[7] 标记邮件已读
```

---

## 五、技术栈详情

| 组件 | 库/工具 | 用途 |
|------|---------|------|
| Gmail API | `google-api-python-client` | 邮件读取与发送 |
| 网页抓取 | `requests` + `beautifulsoup4` | 论文信息获取（默认） |
| 文档解析 | `docling`（可选） | 高级文档解析（预留） |
| AI 总结 | `openai` | OpenAI API 调用 |
| AI 总结 | `google-generativeai`（可选） | Gemini API 调用（预留） |
| 配置管理 | `PyYAML` | YAML 配置解析 |
| 定时调度 | GitHub Actions | 每周自动运行 |
| 测试 | `pytest` | 单元测试 |

---

## 六、扩展性设计

### 6.1 Fetcher 扩展

如需接入 Docling:

```python
# 1. 安装依赖
pip install docling

# 2. 修改 config.yaml
fetcher:
  type: "docling"

# 3. DoclingFetcher 自动生效
```

### 6.2 LLM Provider 扩展

如需接入 Gemini:

```python
# 1. 安装依赖
pip install google-generativeai

# 2. 配置 Secrets
GEMINI_API_KEY: "your-api-key"

# 3. 修改 config.yaml
llm:
  provider: "gemini"
```

---

## 七、后续优化方向

1. **多 LLM 支持**: 完成 GeminiProvider 实现
2. **Fetcher 增强**: 集成 Docling 支持复杂 PDF 解析
3. **智能去重**: 基于标题相似度去重
4. **论文分类**: 自动按研究领域分类
5. **历史存档**: 将报告保存到 Notion/飞书文档
6. **多用户支持**: 支持多个 Gmail 账户

---

## 附录: 参考资源

- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [BeautifulSoup 文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Docling 文档](https://docling-project.github.io/docling/)

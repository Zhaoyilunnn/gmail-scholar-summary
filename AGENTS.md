# AGENTS.md

本文件为在本仓库中运行的智能体提供统一的工作规范。适用于 Gmail 学术新论文自动摘要与周报报告工具项目。

---

## 语言偏好

- 仓库交流与回答默认使用中文，技术术语保留英文。
- 语言表达清晰简洁，注重逻辑和信息密度。
- Markdown 小标题精炼概括，避免冗长修饰。

---

## 构建 / Lint / Test 命令

### Python 环境

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 包含 pytest, ruff, mypy

# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_gmail_client.py

# 运行单个测试函数
pytest tests/test_gmail_client.py -k "test_get_unread_emails"

# 运行并显示详细输出
pytest -v

# 运行并生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 代码检查与格式化

```bash
# Lint 检查 (ruff 替代 flake8)
ruff check src/ tests/
ruff check --fix src/ tests/  # 自动修复

# 代码格式化 (遵循 Google Python Style)
ruff format src/ tests/
black src/ tests/  # 备选

# 类型检查
mypy src/
```

### 本地运行

```bash
# 设置环境变量后运行
python src/main.py

# 带调试日志
DEBUG=1 python src/main.py
```

---

## 代码风格指南

### Imports 规范

- 所有 import 置于文件顶部，按顺序：标准库 → 第三方库 → 本地模块。
- 使用绝对路径导入，禁止深层相对路径如 `../../../utils`。
- 避免循环依赖；公共类型抽出到独立模块。

```python
import json
import logging
from typing import Dict, List, Optional

import requests
from openai import OpenAI

from src.config import Config
from src.gmail_client import GmailClient
```

### 格式化规范

- 使用 **ruff** 和 **black** 格式化。
- 行宽 **88** 字符（black 默认）。
- 使用 **4 空格**缩进，禁止制表符。
- 函数间保留 **2 空行**，类方法间 **1 空行**。
- 文件末尾保留换行。

### 命名约定

- 常量: `MAX_EMAILS = 50`（全大写下划线）
- 变量/函数: `fetch_paper_info()`（蛇形命名）
- 类: `GmailClient`（大驼峰）
- 模块: `paper_fetcher.py`（小写下划线）
- 私有: `_internal_helper()`（下划线前缀）

### 类型注解

- 所有函数参数和返回值必须标注类型。
- 复杂类型使用 `typing` 模块。
- 返回值使用具名结构，避免裸元组。

```python
from dataclasses import dataclass

@dataclass
class PaperSummary:
    title: str
    authors: List[str]
    summary: str
    relevance_score: float

def summarize_paper(title: str, abstract: str) -> PaperSummary:
    """生成论文中文摘要."""
    pass
```

### 注释与文档

- 遵循 **Google Python Style Guide** 的 docstring 格式。
- 注释只写客观功能、单位与用途，**禁止主观修饰**（如 for clarity）。
- 参数必须注明类型和单位。

```python
def fetch_paper_info(url: str, timeout_sec: float = 30.0) -> Dict[str, Any]:
    """从 URL 获取论文信息.

    Args:
        url: 论文页面 URL.
        timeout_sec: 请求超时时间，单位秒，默认 30.

    Returns:
        包含论文信息的字典，字段：title, authors, abstract.

    Raises:
        requests.RequestException: 网络请求失败.
    """
    pass
```

### 错误处理

- 捕获指定异常类型，不裸捕 `Exception`。
- 日志记录因果，不吞错。
- 使用自定义异常类区分业务错误。

```python
class PaperFetchError(Exception):
    """论文获取失败."""
    pass

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    logging.error(f"Request timeout for URL: {url}")
    raise PaperFetchError(f"Timeout fetching {url}")
except requests.RequestException as e:
    logging.error(f"Request failed: {e}")
    raise PaperFetchError(f"Failed to fetch {url}: {e}")
```

### 日志规范

- 使用标准库 `logging`，不用 print。
- 结构化日志，包含上下文信息。
- 级别使用：DEBUG（调试）、INFO（正常）、WARNING（警告）、ERROR（错误）。

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing {len(emails)} emails from label: {label}")
logger.debug(f"Email ID: {msg_id}, Subject: {subject}")
logger.error(f"Failed to parse paper: {url}", exc_info=True)
```

---

## 项目结构

```
gmail-scholar-summary/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── config.py
│   ├── gmail_client.py
│   ├── paper_fetcher.py
│   ├── summarizer.py
│   ├── report_generator.py
│   └── main.py
├── tests/                  # 测试
│   ├── __init__.py
│   ├── test_gmail_client.py
│   ├── test_paper_fetcher.py
│   └── conftest.py         # pytest fixtures
├── .github/workflows/      # CI/CD
├── config/                 # 配置模板
├── scripts/                # 辅助脚本
├── requirements.txt
├── requirements-dev.txt
└── AGENTS.md
```

---

## 测试规范

- 测试文件命名：`test_<module>.py`。
- 测试函数命名：`test_<functionality>`。
- 使用 `pytest` 和 `unittest.mock`。
- 外部 API 调用必须 Mock。

```python
import pytest
from unittest.mock import Mock

def test_get_unread_emails_empty():
    """测试无未读邮件时返回空列表."""
    mock_service = Mock()
    mock_service.users().messages().list.return_value.execute.return_value = {
        'messages': []
    }
    client = GmailClient(credentials=Mock())
    client.service = mock_service
    result = client.get_unread_scholar_emails("Scholar Alerts")
    assert result == []
```

---

## Git 提交规范

- 使用中文描述变更内容。
- 格式：`[<类型>] <描述>`。
- 类型：feat, fix, docs, style, refactor, test, chore。

```
[feat] 添加 Gmail API 客户端类
[fix] 修复论文链接提取正则表达式
[test] 添加 paper_fetcher 单元测试
```

---

## 依赖管理

- `requirements.txt`：生产依赖，指定最低版本。
- `requirements-dev.txt`：开发依赖（测试、lint）。
- 新增依赖需在 PR 中说明用途。

---

最后更新：2026-02-17

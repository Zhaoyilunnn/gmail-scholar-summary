"""报告生成器模块.

生成 Markdown 和 HTML 格式的周报.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.config import ReportConfig

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器.

    生成格式化的学术周报.
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """初始化报告生成器.

        Args:
            config: 报告配置，使用默认配置如果为 None.
        """
        self.config = config or ReportConfig()

    def generate_markdown(self, papers: List[Dict]) -> str:
        """生成 Markdown 格式报告.

        Args:
            papers: 论文列表，每个包含 title, authors, summary 等字段.

        Returns:
            Markdown 格式报告.
        """
        if not papers:
            return self._generate_empty_report()

        lines = []

        # 标题
        date_str = datetime.now().strftime("%Y-%m-%d")
        lines.append(f"# 学术周报 - {date_str}")
        lines.append("")

        # 统计信息
        lines.append(f"本周共处理 **{len(papers)}** 篇论文")
        lines.append("")

        # 论文列表
        lines.append("## 论文列表")
        lines.append("")

        for i, paper in enumerate(papers, 1):
            lines.append(self._format_paper_markdown(i, paper))
            lines.append("")

        return "\n".join(lines)

    def generate_html(self, papers: List[Dict]) -> str:
        """生成 HTML 格式报告.

        Args:
            papers: 论文列表.

        Returns:
            HTML 格式报告.
        """
        if not papers:
            return self._generate_empty_html_report()

        date_str = datetime.now().strftime("%Y-%m-%d")

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            f"<title>学术周报 - {date_str}</title>",
            self._get_html_styles(),
            "</head>",
            "<body>",
            f"<h1>学术周报 - {date_str}</h1>",
            f'<p class="summary">本周共处理 <strong>{len(papers)}</strong> 篇论文</p>',
            '<div class="papers">',
        ]

        for i, paper in enumerate(papers, 1):
            html_parts.append(self._format_paper_html(i, paper))

        html_parts.extend(
            [
                "</div>",
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)

    def _format_paper_markdown(self, index: int, paper: Dict) -> str:
        """格式化单篇论文为 Markdown.

        Args:
            index: 序号.
            paper: 论文数据.

        Returns:
            Markdown 字符串.
        """
        lines = []

        # 标题和链接
        title = paper.get("title", "未知标题")
        url = paper.get("url", "")
        lines.append(f"### {index}. [{title}]({url})")
        lines.append("")

        # 作者
        authors = paper.get("authors", [])
        if authors:
            authors_str = ", ".join(authors)
            lines.append(f"**作者**: {authors_str}")
            lines.append("")

        # 年份和 venue
        year = paper.get("year", "")
        venue = paper.get("venue", "")
        if year or venue:
            meta_parts = []
            if year:
                meta_parts.append(f"年份: {year}")
            if venue:
                meta_parts.append(f"发表: {venue}")
            lines.append(f"**{', '.join(meta_parts)}**")
            lines.append("")

        # 一句话总结
        summary = paper.get("summary", "")
        if summary:
            lines.append(f"📋 **一句话总结**: {summary}")
            lines.append("")

        # 研究背景
        background = paper.get("background", "")
        if background:
            lines.append(f"🔍 **研究背景**: {background}")
            lines.append("")

        # 核心方法
        method = paper.get("method", "")
        if method:
            lines.append(f"💡 **核心方法**: {method}")
            lines.append("")

        # 主要结果
        results = paper.get("results", "")
        if results:
            lines.append(f"📊 **主要结果**: {results}")
            lines.append("")

        # 相关度评分（仅在启用时显示）
        score = paper.get("relevance_score")
        if score is not None:
            lines.append(f"⭐ **相关度评分**: {score}/10")
            lines.append("")

        return "\n".join(lines)

    def _format_paper_html(self, index: int, paper: Dict) -> str:
        """格式化单篇论文为 HTML.

        Args:
            index: 序号.
            paper: 论文数据.

        Returns:
            HTML 字符串.
        """
        title = paper.get("title", "未知标题")
        url = paper.get("url", "#")
        authors = ", ".join(paper.get("authors", []))
        year = paper.get("year", "")
        venue = paper.get("venue", "")
        summary = paper.get("summary", "")
        background = paper.get("background", "")
        method = paper.get("method", "")
        results = paper.get("results", "")
        score = paper.get("relevance_score")

        html_parts = [
            '<div class="paper">',
            f'<h3>{index}. <a href="{url}">{title}</a></h3>',
        ]

        if authors:
            html_parts.append(
                f'<p class="authors"><strong>作者:</strong> {authors}</p>'
            )

        meta_parts = []
        if year:
            meta_parts.append(f"年份: {year}")
        if venue:
            meta_parts.append(f"发表: {venue}")
        if meta_parts:
            html_parts.append(
                f'<p class="meta"><strong>{", ".join(meta_parts)}</strong></p>'
            )

        if summary:
            html_parts.append(
                f'<p class="summary">📋 <strong>一句话总结:</strong> {summary}</p>'
            )

        if background:
            html_parts.append(
                f'<p class="background">🔍 <strong>研究背景:</strong> {background}</p>'
            )

        if method:
            html_parts.append(
                f'<p class="method">💡 <strong>核心方法:</strong> {method}</p>'
            )

        if results:
            html_parts.append(
                f'<p class="results">📊 <strong>主要结果:</strong> {results}</p>'
            )

        if score is not None:
            html_parts.append(
                f'<p class="score">⭐ <strong>相关度评分:</strong> {score}/10</p>'
            )

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _generate_empty_report(self) -> str:
        """生成空报告."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""# 学术周报 - {date_str}

本周没有新论文需要处理。

---

*此报告由 Gmail Scholar Summary 自动生成*
"""

    def _generate_empty_html_report(self) -> str:
        """生成空 HTML 报告."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>学术周报 - {date_str}</title>
{self._get_html_styles()}
</head>
<body>
<h1>学术周报 - {date_str}</h1>
<p class="summary">本周没有新论文需要处理。</p>
<hr>
<p class="footer">此报告由 Gmail Scholar Summary 自动生成</p>
</body>
</html>
"""

    def _get_html_styles(self) -> str:
        """获取 HTML 样式."""
        return """<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    color: #333;
}
h1 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}
h3 {
    color: #34495e;
    margin-top: 30px;
}
.paper {
    background: #f8f9fa;
    border-left: 4px solid #3498db;
    padding: 15px;
    margin: 20px 0;
    border-radius: 4px;
}
.paper h3 {
    margin-top: 0;
}
.paper h3 a {
    color: #2980b9;
    text-decoration: none;
}
.paper h3 a:hover {
    text-decoration: underline;
}
.authors {
    color: #666;
    font-style: italic;
}
.meta {
    color: #888;
    font-size: 0.9em;
}
.score {
    color: #e74c3c;
    font-weight: bold;
}
.summary {
    font-size: 1.1em;
    margin: 20px 0;
}
.footer {
    color: #999;
    font-size: 0.9em;
    text-align: center;
    margin-top: 40px;
}
</style>"""

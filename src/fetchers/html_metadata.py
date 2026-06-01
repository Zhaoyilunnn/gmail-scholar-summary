"""HTML metadata 提取工具."""

import re
from typing import List

from bs4 import BeautifulSoup


def normalize_whitespace(text: str) -> str:
    """归一化空白字符.

    Args:
        text: 原始文本.

    Returns:
        空白字符归一化后的文本.
    """
    return re.sub(r"\s+", " ", text).strip()


def get_meta_content(soup: BeautifulSoup, names: List[str]) -> str:
    """从 meta 标签中获取第一个匹配的 content.

    Args:
        soup: BeautifulSoup 对象.
        names: meta name/property 列表.

    Returns:
        第一个非空 content，未找到时返回空字符串.
    """
    values = get_all_meta_contents(soup, names)
    return values[0] if values else ""


def get_all_meta_contents(soup: BeautifulSoup, names: List[str]) -> List[str]:
    """从 meta 标签中获取所有匹配的 content.

    Args:
        soup: BeautifulSoup 对象.
        names: meta name/property 列表.

    Returns:
        去重后的 content 列表.
    """
    wanted_names = {name.lower() for name in names}
    contents = []
    seen = set()

    for meta in soup.find_all("meta"):
        meta_name = str(meta.get("name", "")).lower()
        meta_property = str(meta.get("property", "")).lower()
        if meta_name not in wanted_names and meta_property not in wanted_names:
            continue

        content = normalize_whitespace(str(meta.get("content", "")))
        if content and content not in seen:
            contents.append(content)
            seen.add(content)

    return contents


def get_text_by_selectors(soup: BeautifulSoup, selectors: List[str]) -> str:
    """按 CSS selector 获取第一个非空文本.

    Args:
        soup: BeautifulSoup 对象.
        selectors: CSS selector 列表.

    Returns:
        第一个非空文本，未找到时返回空字符串.
    """
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = normalize_whitespace(elem.get_text(" ", strip=True))
            if text:
                return text
    return ""

#!/usr/bin/env python3
"""Lightweight checks for Chinese AI-comic WeChat article drafts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CLICHES = {
    r"不是.{0,40}而是": "疑似翻案句式",
    r"并非.{0,40}而是": "疑似翻案句式",
    r"你以为.{0,40}其实": "疑似翻案句式",
    r"先说结论|说白了|说穿了": "模板化路标",
    r"赋能|重塑|颠覆|底层逻辑|时代浪潮|生态闭环|重新定义": "商业或模型惯用词",
    r"降本增效": "需要改成可核实的时间、成本或人力变化",
}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path)
    parser.add_argument(
        "--allow-no-sources",
        action="store_true",
        help="Do not warn when a long draft has no source section.",
    )
    args = parser.parse_args()

    if not args.draft.is_file():
        print(f"ERROR: file not found: {args.draft}")
        return 2

    text = args.draft.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("稿件为空")
    if re.search(r"\bTODO\b|\[待补|待核实", text, re.I):
        errors.append("仍有 TODO 或待补占位符")

    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", text))
    has_sources_heading = bool(
        re.search(r"^#{1,4}\s*(资料来源|参考资料|参考来源|来源)\s*$", text, re.M)
    )
    url_count = len(re.findall(r"https?://", text))
    if chinese_chars >= 1200 and not args.allow_no_sources:
        if not has_sources_heading:
            warnings.append("长篇现实稿未发现资料来源章节")
        elif url_count < 3:
            warnings.append("资料来源少于 3 个链接，请确认能否支撑核心判断")

    if "—" in text or "–" in text:
        warnings.append("发现破折号，检查是否可以改成普通句子")

    for pattern, label in CLICHES.items():
        for match in re.finditer(pattern, text):
            snippet = match.group(0).replace("\n", " ")
            warnings.append(
                f"第 {line_number(text, match.start())} 行：{label}：{snippet[:60]}"
            )

    digit_claims = re.findall(
        r"(?<![#\w])\d+(?:\.\d+)?\s*(?:%|％|元|万元|亿元|小时|分钟|天|人|集|倍)",
        text,
    )
    if digit_claims and url_count == 0:
        warnings.append("稿件含数字事实但没有链接来源")

    print(f"Chinese characters: {chinese_chars}")
    print(f"Source links: {url_count}")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    if not errors and not warnings:
        print("OK: no issues found")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

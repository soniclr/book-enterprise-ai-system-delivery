#!/usr/bin/env python3
"""Validate the independent enterprise AI book manuscript."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT
MANUSCRIPT = BOOK / "manuscript"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    chapter_files = sorted(MANUSCRIPT.glob("part-*/*.md"))
    short_prose_paragraphs = 0

    if len(chapter_files) != 20:
        fail(f"expected 20 chapter files, found {len(chapter_files)}", errors)

    seen_numbers: set[int] = set()
    total_chars = 0

    for path in chapter_files:
        text = path.read_text(encoding="utf-8")
        total_chars += len(text)

        heading = re.search(r"^# 第\s*(\d+)\s*章\s+(.+)$", text, re.MULTILINE)
        if not heading:
            fail(f"missing numbered H1: {path.relative_to(ROOT)}", errors)
            continue

        number = int(heading.group(1))
        if number in seen_numbers:
            fail(f"duplicate chapter number {number}: {path.relative_to(ROOT)}", errors)
        seen_numbers.add(number)

        if len(text) < 2400:
            fail(f"reader-first chapter shorter than 2400 characters: {path.relative_to(ROOT)}", errors)

        old_wrappers = (
            "> **这一章要解决什么问题**",
            "**先把结论说清楚：**",
            "## 如果你正在做项目",
            "深入一层：",
            "### 动手试一遍",
            "### 可以直接使用的工具",
        )
        if any(wrapper in text for wrapper in old_wrappers):
            fail(f"course-style wrapper remains: {path.relative_to(ROOT)}", errors)

        if re.search(r"\bOwner\b", text):
            fail(f"untranslated Owner remains in chapter prose: {path.relative_to(ROOT)}", errors)

        if re.search(r"\b(Agent|POC|RAG|ROI|Demo|FDE)\b", text):
            fail(f"avoidable English project shorthand remains in main reading: {path.relative_to(ROOT)}", errors)

        if re.search(r"^### ", text, re.MULTILINE):
            fail(f"lecture-like H3 heading remains in main reading: {path.relative_to(ROOT)}", errors)

        if re.search(r"^#### ", text, re.MULTILINE):
            fail(f"lecture-like H4 heading remains in main reading: {path.relative_to(ROOT)}", errors)

        if any(phrase in text for phrase in ("说到第一", "重点看AI", "先看不要", "到了模式")):
            fail(f"mechanical transition remains in main reading: {path.relative_to(ROOT)}", errors)

        if any(token in text for token in ("：。", "；。", "。。", "。；")):
            fail(f"broken punctuation after reader rewrite: {path.relative_to(ROOT)}", errors)

        fourth_draft_artifacts = (
            "SI概念验证",
            "完整完整流程",
            "后。系统",
            "时。系统",
            "Human-in-the-loop",
            "A3智能体",
            "关键权限放行条件不得放行",
            "<!-- reader-third-draft-",
        )
        if any(artifact in text for artifact in fourth_draft_artifacts):
            fail(f"known third-draft expression artifact remains: {path.relative_to(ROOT)}", errors)

        short_prose_paragraphs += sum(
            1
            for line in text.splitlines()
            if 1 <= len(line.strip()) <= 34
            and line.strip().endswith(("。", "！", "？", "："))
            and not line.lstrip().startswith(("#", ">", "|", "-", "*", "!", "`"))
            and not re.match(r"^\d+\. ", line.strip())
        )

        if "启明科技" not in text:
            fail(f"missing continuous case reference: {path.relative_to(ROOT)}", errors)

        if len(re.findall(r"^## ", text, re.MULTILINE)) < 5:
            fail(f"chapter has fewer than five major sections: {path.relative_to(ROOT)}", errors)

        if len(re.findall(r"^## ", text, re.MULTILINE)) > 12:
            fail(f"chapter has more than twelve major sections: {path.relative_to(ROOT)}", errors)

        if text.count("```") % 2:
            fail(f"unclosed fenced code block: {path.relative_to(ROOT)}", errors)

        if re.search(r"\b(TODO|TBD|PLACEHOLDER)\b|\[待写\]", text, re.IGNORECASE):
            fail(f"placeholder remains: {path.relative_to(ROOT)}", errors)

    expected_numbers = set(range(1, 21))
    if seen_numbers != expected_numbers:
        fail(
            f"chapter numbers mismatch: expected 1-20, found {sorted(seen_numbers)}",
            errors,
        )

    if not 85000 <= total_chars <= 110000:
        fail(f"reader-first main text outside 85k-110k character band: {total_chars}", errors)

    if short_prose_paragraphs > 230:
        fail(
            f"fourth-draft short prose paragraph count exceeds 230: {short_prose_paragraphs}",
            errors,
        )

    deep_appendix = BOOK / "appendices" / "H-technical-deep-dives.md"
    workbook_appendix = BOOK / "appendices" / "I-chapter-workbook.md"
    if not deep_appendix.exists() or deep_appendix.stat().st_size < 45000:
        fail("technical deep-reading appendix is missing or unexpectedly short", errors)
    if not workbook_appendix.exists() or workbook_appendix.stat().st_size < 15000:
        fail("chapter workbook appendix is missing or unexpectedly short", errors)
    if deep_appendix.exists() and len(re.findall(r"^## 第\s*\d+\s*章", deep_appendix.read_text(encoding="utf-8"), re.MULTILINE)) != 20:
        fail("technical deep-reading appendix does not contain all 20 chapters", errors)
    if workbook_appendix.exists() and len(re.findall(r"^## 第\s*\d+\s*章", workbook_appendix.read_text(encoding="utf-8"), re.MULTILINE)) != 20:
        fail("chapter workbook appendix does not contain all 20 chapters", errors)

    sentence_lengths: list[int] = []
    for path in chapter_files:
        in_code = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("```"):
                in_code = not in_code
                continue
            stripped = line.strip()
            if (
                in_code
                or not stripped
                or stripped.startswith(("#", "|", "- ", "* ", "![", "[^"))
                or re.match(r"^\d+\. ", stripped)
            ):
                continue
            if stripped.startswith(">"):
                stripped = stripped.lstrip("> ").replace("**", "")
            sentence_lengths.extend(
                len(re.sub(r"\s+", "", sentence))
                for sentence in re.split(r"[。！？]", stripped)
                if len(sentence.strip()) > 3
            )

    if sentence_lengths:
        ordered = sorted(sentence_lengths)
        p90 = ordered[int(len(ordered) * 0.9) - 1]
        long_ratio = sum(length >= 55 for length in ordered) / len(ordered)
        if p90 > 50:
            fail(f"reader-rewrite sentence P90 exceeds 50 characters: {p90}", errors)
        if long_ratio >= 0.08:
            fail(f"reader-rewrite long sentence ratio exceeds 8%: {long_ratio:.1%}", errors)

    authored_roots = [
        BOOK / "manuscript",
        BOOK / "cases",
        BOOK / "appendices",
        BOOK / "tools",
        BOOK / "publication",
    ]
    authored_files = sorted(
        path for root in authored_roots for path in root.rglob("*.md")
    )
    authored_text = "\n".join(path.read_text(encoding="utf-8") for path in authored_files)
    if "七要素" in authored_text:
        fail("deprecated framework name 七要素 remains in authored content", errors)
    if "计划中的技术卡" in authored_text:
        fail("versioned technical cards are still marked as planned", errors)
    if authored_text.count("[^ch") < 8:
        fail("fewer than eight chapter citation markers", errors)

    references = (BOOK / "appendices" / "E-references.md").read_text(encoding="utf-8")
    if len(re.findall(r"^\d+\. ", references, re.MULTILINE)) < 20:
        fail("reference list contains fewer than twenty versioned entries", errors)

    figure_list = (BOOK / "appendices" / "G-figure-list.md").read_text(encoding="utf-8")
    if len(re.findall(r"^\|\s*\d+\s*\|", figure_list, re.MULTILINE)) < 60:
        fail("generated figure list contains fewer than sixty entries", errors)

    markdown_files = sorted(
        path for path in BOOK.rglob("*.md") if "archive" not in path.parts
    )
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        if text.count("```") % 2:
            fail(f"unclosed fenced code block: {path.relative_to(ROOT)}", errors)
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            if not clean_target:
                continue
            resolved = (path.parent / clean_target).resolve()
            if not resolved.exists():
                fail(
                    f"broken relative link in {path.relative_to(ROOT)}: {target}",
                    errors,
                )

    if errors:
        print("BOOK MANUSCRIPT VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("BOOK MANUSCRIPT VALIDATION: PASS")
    print(f"- chapters: {len(chapter_files)}")
    print(f"- book markdown files: {len(markdown_files)}")
    print(f"- chapter characters: {total_chars}")
    print(f"- reader sentence P90: {p90}")
    print(f"- sentences >=55 chars: {long_ratio:.1%}")
    print(f"- short prose paragraphs: {short_prose_paragraphs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

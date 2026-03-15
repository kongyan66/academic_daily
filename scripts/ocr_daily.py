#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Fetch daily OCR-related arXiv papers and write daily summary.

Usage:
  python3 ocr_daily.py

Outputs the summary to stdout (plain text) and appends to
/home/administrator/.openclaw/workspace/ocr-daily/YYYY-MM-DD.md
"""

import os
import sys
import textwrap
import requests
import datetime as dt
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
KEYWORDS = [
    'OCR',
    '"text recognition"',
    '"scene text"',
    '"document understanding"',
]
PREFERRED_CATS = ["cs.CV", "cs.AI", "eess.IV"]

OUT_DIR = "/home/administrator/.openclaw/workspace/ocr-daily"


def _iso_to_dt(s: str) -> dt.datetime:
    # arXiv uses Z suffix
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def _topic_from_title(title: str) -> str:
    t = title.lower()
    if "scene text" in t:
        return "场景文本识别"
    if "document" in t:
        return "文档理解"
    if "recognition" in t:
        return "文本识别"
    if "ocr" in t:
        return "OCR"
    return "OCR/文本识别"


def fetch_entries(max_results=200):
    query = " OR ".join([f"all:{k}" for k in KEYWORDS])
    params = {
        "search_query": f"({query})",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    resp = requests.get(ARXIV_API, params=params, timeout=30)
    resp.raise_for_status()

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(resp.text)
    entries = []
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns).strip().replace("\n", " ")
        summary = entry.findtext("atom:summary", default="", namespaces=ns).strip().replace("\n", " ")
        published = entry.findtext("atom:published", default="", namespaces=ns)
        updated = entry.findtext("atom:updated", default="", namespaces=ns)
        link = entry.findtext("atom:id", default="", namespaces=ns)
        authors = [a.findtext("atom:name", default="", namespaces=ns) for a in entry.findall("atom:author", ns)]
        categories = [c.attrib.get("term") for c in entry.findall("atom:category", ns)]

        # arXiv id
        arxiv_id = link.split("/abs/")[-1] if "/abs/" in link else link

        entries.append({
            "title": title,
            "summary": summary,
            "published": published,
            "updated": updated,
            "link": link,
            "authors": authors,
            "categories": categories,
            "arxiv_id": arxiv_id,
        })
    return entries


def filter_and_sort(entries):
    now = dt.datetime.now(dt.timezone.utc)
    day_ago = now - dt.timedelta(hours=24)

    filtered = []
    for e in entries:
        if not e.get("published"):
            continue
        try:
            pub_dt = _iso_to_dt(e["published"])
        except Exception:
            continue
        if pub_dt < day_ago:
            continue
        e["published_dt"] = pub_dt
        # priority by category
        cats = e.get("categories", [])
        preferred = any(c in PREFERRED_CATS for c in cats)
        e["priority"] = 0 if preferred else 1
        filtered.append(e)

    filtered.sort(key=lambda x: (x["priority"], -x["published_dt"].timestamp()))
    return filtered


def format_entry(e):
    title = e["title"]
    arxiv_id = e["arxiv_id"]
    link = e["link"]
    authors = ", ".join(e["authors"]) if e["authors"] else ""
    topic = _topic_from_title(title)

    line1 = f"- 标题：{title}\n  作者：{authors}\n  链接：{link}\n  arXiv：{arxiv_id}"
    line2 = f"  贡献亮点：围绕{topic}提出/分析新方法或改进方案，面向OCR/文本识别任务。"
    return line1 + "\n" + line2


def main():
    entries = fetch_entries()
    entries = filter_and_sort(entries)

    today = dt.datetime.now().strftime("%Y-%m-%d")
    header = f"## {today} OCR/文本识别 arXiv 日报"

    if not entries:
        summary = f"{header}\n\n今日无新论文"
    else:
        parts = [header, ""]
        for e in entries:
            parts.append(format_entry(e))
            parts.append("")
        summary = "\n".join(parts).rstrip() + "\n"

    # write/append
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{today}.md")
    with open(out_path, "a", encoding="utf-8") as f:
        if os.path.getsize(out_path) > 0:
            f.write("\n")
        f.write(summary)
        f.write("\n")

    # stdout
    sys.stdout.write(summary.strip())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/home/administrator/.openclaw/workspace")
OCR_DIR = WORKSPACE / "ocr-daily"
OUTPUT_DIR = WORKSPACE / "academic_daily" / "docs"
DAILY_DIR = OUTPUT_DIR / "daily"

TITLE = "学术资源共享"
SUBTITLE = "论文追踪 · 专题调研 · 项目管理"


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )


def simple_md_to_html(md: str) -> str:
    lines = md.strip().splitlines()
    out = []
    in_ul = False
    for line in lines:
        line = line.rstrip()
        if line.startswith("# "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h1>{html_escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<h2>{html_escape(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html_escape(line[2:].strip())}</li>")
        elif line.strip() == "":
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("<br />")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{html_escape(line)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def summarize(md: str) -> str:
    if "今日无新论文" in md:
        return "今日无新论文"
    # grab first non-empty line after title
    lines = [l.strip() for l in md.splitlines() if l.strip()]
    if not lines:
        return ""
    if len(lines) >= 2:
        return lines[1][:120]
    return lines[0][:120]


def count_papers(md: str) -> int:
    if "今日无新论文" in md:
        return 0
    # count list items
    return len([l for l in md.splitlines() if l.strip().startswith("- ")])


def build():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(OCR_DIR.glob("*.md"), reverse=True)
    reports = []
    total_papers = 0
    for f in files:
        md = f.read_text(encoding="utf-8")
        date = f.stem
        total_papers += count_papers(md)
        reports.append({
            "date": date,
            "summary": summarize(md),
            "filename": f"daily/{date}.html",
            "md": md,
        })

        # daily page
        daily_html = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{date} OCR 每日摘要</title>
  <link rel=\"stylesheet\" href=\"../style.css\" />
</head>
<body>
  <div class=\"page\">
    <header class=\"top\">
      <a class=\"back\" href=\"../index.html\">← 返回首页</a>
      <h1>{date} OCR 每日摘要</h1>
    </header>
    <section class=\"card\">
      {simple_md_to_html(md)}
    </section>
  </div>
</body>
</html>
"""
        (DAILY_DIR / f"{date}.html").write_text(daily_html, encoding="utf-8")

    last_update = reports[0]["date"] if reports else "-"
    report_count = len(reports)

    recent_items = "\n".join([
        f"""
        <div class=\"list-item\">
          <div class=\"date\">{r['date']}</div>
          <div class=\"title\">OCR 每日摘要</div>
          <div class=\"desc\">{html_escape(r['summary'])}</div>
          <a class=\"tag\" href=\"{r['filename']}\">查看</a>
        </div>
        """ for r in reports[:10]
    ])

    index_html = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{TITLE}</title>
  <link rel=\"stylesheet\" href=\"style.css\" />
</head>
<body>
  <div class=\"hero\">
    <div class=\"hero-inner\">
      <div class=\"logo\">📚</div>
      <h1>{TITLE}</h1>
      <p>{SUBTITLE}</p>
    </div>
  </div>

  <div class=\"page\">
    <section class=\"cards\">
      <div class=\"card feature\">
        <div class=\"icon\">📄</div>
        <h3>arXiv 每日分析</h3>
        <p>OCR 领域论文追踪</p>
      </div>
      <div class=\"card feature\">
        <div class=\"icon\">🔬</div>
        <h3>专题调研</h3>
        <p>深度技术调研报告</p>
      </div>
      <div class=\"card feature\">
        <div class=\"icon\">📌</div>
        <h3>项目看板</h3>
        <p>研究项目进度追踪</p>
      </div>
    </section>

    <section class=\"stats\">
      <div class=\"stat\"><div class=\"num\">{total_papers}</div><div class=\"label\">累计论文</div></div>
      <div class=\"stat\"><div class=\"num\">{report_count}</div><div class=\"label\">日报数量</div></div>
      <div class=\"stat\"><div class=\"num\">0</div><div class=\"label\">调研专题</div></div>
      <div class=\"stat\"><div class=\"num\">1</div><div class=\"label\">进行中项目</div></div>
    </section>

    <section class=\"updates\">
      <div class=\"updates-header\">
        <div class=\"title\">最近更新</div>
        <div class=\"hint\">最近一次更新：{last_update}</div>
      </div>
      <div class=\"list\">{recent_items or '<div class="empty">暂无更新</div>'}</div>
    </section>
  </div>
</body>
</html>
"""

    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")


if __name__ == "__main__":
    build()

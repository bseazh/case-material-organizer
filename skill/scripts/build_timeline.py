#!/usr/bin/env python3
"""Render the confirmed Excel timeline as deterministic, print-ready HTML."""

from __future__ import annotations

import argparse
import html
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from openpyxl import load_workbook


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def split_cn(value: object) -> list[str]:
    return [part.strip() for part in re.split(r"[；;\n]+", str(value or "")) if part.strip()]


def year_of(value: object) -> str:
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return match.group(0) if match else "时间待核"


def date_parts(value: object) -> tuple[str, str]:
    text = str(value or "时间待核")
    year = year_of(text)
    if year == "时间待核":
        return "待核", "日期未明"
    short = text.replace(year + "-", "", 1).replace(year, "", 1).strip(" -")
    short = re.sub(r"至(?:19|20)\d{2}-", "—", short)
    short = short.replace("至", "—").replace("起", " 起").replace("-", ".")
    return year, short or year


def link_for(path: Path, output_dir: Path) -> str:
    relative = Path(os.path.relpath(path, output_dir))
    return "/".join(quote(part) for part in relative.parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="从案件材料汇总.xlsx生成时间轴HTML")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--out", type=Path, default=Path("时间轴.html"))
    parser.add_argument("--title", default="案件材料时间轴")
    parser.add_argument("--subtitle", default="已归档材料整理结果 · 事实中性呈现")
    parser.add_argument("--notice", default="仅依据当前已归档材料整理")
    args = parser.parse_args()

    wb = load_workbook(args.workbook, data_only=True, read_only=True)
    ws = wb["案件时间轴"]
    headers = [cell.value for cell in ws[3]]
    events = []
    for values in ws.iter_rows(min_row=4, values_only=True):
        if not any(value is not None for value in values):
            continue
        event = dict(zip(headers, values))
        events.append(event)
    events.sort(key=lambda event: (str(event.get("日期") or "9999"), str(event.get("事件") or "")))

    overview_ws = wb["案件概览"]
    overview = {
        str(overview_ws.cell(row, 1).value): str(overview_ws.cell(row, 2).value or "")
        for row in range(4, overview_ws.max_row + 1)
        if overview_ws.cell(row, 1).value
    }
    issue_ws = wb["问题与待补材料"]
    issue_count = sum(
        1 for row in issue_ws.iter_rows(min_row=4, values_only=True)
        if any(value is not None for value in row)
    )
    years = [year_of(event.get("日期")) for event in events]
    year_counts = Counter(years)
    known_years = {year for year in years if year != "时间待核"}
    material_names = {name for event in events for name in split_cn(event.get("相关材料"))}
    archive_index: dict[str, list[Path]] = {}
    for folder in ("001 主体信息", "002 基础资料", "003 委托材料", "004 类案及法律检索", "005 法律文书"):
        base = args.workbook.parent / folder
        if base.exists():
            for path in base.rglob("*"):
                if path.is_file():
                    archive_index.setdefault(path.name, []).append(path)

    cards: list[str] = []
    current_year = None
    for event in events:
        event_year = year_of(event.get("日期"))
        if event_year != current_year:
            current_year = event_year
            cards.append(
                f'<div class="year-break"><span>{esc(event_year)}</span>'
                f'<b>{year_counts[event_year]} 个事件</b></div>'
            )
        year, date = date_parts(event.get("日期"))
        names = split_cn(event.get("相关材料"))
        links = []
        for name in names:
            candidates = archive_index.get(name, [])
            if len(candidates) == 1:
                links.append(f'<li><a href="{link_for(candidates[0], args.out.parent.resolve())}">{esc(name)}</a></li>')
            else:
                links.append(f'<li>{esc(name)}</li>')
        path_links = "".join(links)
        attachments = ""
        print_paths = ""
        if names:
            attachments = (
                f'<details><summary>查看 {len(names)} 份相关材料</summary>'
                f'<ul class="attachments">{path_links}</ul></details>'
            )
            print_paths = f'<p class="print-paths"><b>相关材料</b>{esc("；".join(names))}</p>'
        check = str(event.get("待确认事项") or "无")
        check_badge = '<span class="precision">有待确认事项</span>' if check not in {"无", "", "无。"} else ""
        cards.append(f'''
<article class="event material">
  <div class="date-block"><span>{esc(year)}</span><strong>{esc(date)}</strong></div>
  <div class="rail"><i></i></div>
  <section>
    <div class="event-top"><span class="tone">材料整理事件</span>{check_badge}</div>
    <h2>{esc(event.get("事件"))}</h2>
    <dl><div><dt>相关主体</dt><dd>{esc(event.get("相关人员/公司"))}</dd></div></dl>
    <p class="check"><b>待确认</b>{esc(check)}</p>
    {attachments}
    {print_paths}
  </section>
</article>''')

    summary_labels = [("起因", "01"), ("过程", "02"), ("争议", "03"), ("现状", "04"), ("缺口", "05")]
    summary_html = "".join(
        f'<section><span>{number}</span><h3>{label}</h3><p>{esc(overview.get(label, "待补充"))}</p></section>'
        for label, number in summary_labels
    )
    dated_events = [event for event in events if year_of(event.get("日期")) != "时间待核"]
    first_date = esc(dated_events[0].get("日期") if dated_events else "-")
    last_date = esc(dated_events[-1].get("日期") if dated_events else "-")
    undated_note = f"（另有 {len(events) - len(dated_events)} 项日期待确认）" if len(dated_events) != len(events) else ""
    document = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(args.title)}</title>
<style>
:root{{--ink:#152b3a;--navy:#173f5f;--teal:#16817a;--amber:#b7791f;--red:#b83a3a;--gray:#64727d;--paper:#fff;--ground:#edf1f3;--line:#b7c5cc}}
*{{box-sizing:border-box}}html{{background:var(--ground)}}body{{margin:0;color:var(--ink);background:var(--ground);font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif;letter-spacing:0}}
main{{width:min(1180px,calc(100% - 40px));margin:0 auto;padding:48px 0 72px}}
.hero{{padding:32px 36px 30px;background:var(--navy);color:#fff;border-top:8px solid var(--teal)}}
.eyebrow{{margin:0 0 14px;color:#b9ded9;font-size:13px;font-weight:700}}h1{{margin:0;font-size:34px;line-height:1.25;letter-spacing:0}}.subtitle{{margin:12px 0 0;color:#d8e5ec;font-size:15px}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);margin-top:28px;border-top:1px solid #557086}}
.metric{{padding:18px 18px 0 0}}.metric b{{display:block;font-size:27px;color:#fff}}.metric span{{color:#bad0dc;font-size:12px}}
.notice{{display:flex;justify-content:space-between;gap:18px;margin-top:24px;padding-top:18px;border-top:1px solid #557086;color:#d8e5ec;font-size:12px}}
.overview{{margin:28px 0 38px;padding:28px 34px;background:#fff;border:1px solid #d5dde2;border-top:4px solid var(--amber)}}
.section-title{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:24px}}.section-title h2{{margin:0;font-size:22px;color:var(--navy)}}.section-title p{{margin:0;color:var(--gray);font-size:12px}}
.summary-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:0}}.summary-grid section{{padding:0 18px;border-left:1px solid #dfe5e8}}.summary-grid section:first-child{{padding-left:0;border-left:0}}.summary-grid span{{font:700 12px Arial;color:var(--teal)}}.summary-grid h3{{margin:6px 0 10px;font-size:15px;color:var(--navy)}}.summary-grid p{{margin:0;font-size:12px;line-height:1.7;color:#42535e}}
.legend{{display:flex;flex-wrap:wrap;gap:18px;margin:0 0 20px;padding:0 0 18px;border-bottom:1px solid #cbd5da;font-size:12px;color:#50616c}}.legend span:before{{content:"";display:inline-block;width:9px;height:9px;margin-right:7px;background:var(--teal)}}.legend .l2:before{{background:var(--amber)}}.legend .l3:before{{background:var(--navy)}}.legend .l4:before{{background:var(--gray)}}.legend .l5:before{{background:var(--red)}}
.timeline{{position:relative}}.year-break{{display:flex;align-items:center;gap:18px;margin:34px 0 18px 214px;color:var(--navy)}}.year-break:after{{content:"";height:1px;flex:1;background:#aebdc5}}.year-break span{{font-size:25px;font-weight:800}}.year-break b{{font-size:12px;color:var(--gray);white-space:nowrap}}
.event{{--accent:var(--teal);display:grid;grid-template-columns:180px 68px 1fr;align-items:stretch;margin-bottom:18px}}.event.statement{{--accent:var(--amber)}}.event.company{{--accent:var(--navy)}}.event.objective{{--accent:var(--gray)}}
.date-block{{align-self:start;padding:12px 14px;border-left:4px solid var(--accent);background:#fff;text-align:right}}.date-block span{{display:block;font-size:12px;color:var(--gray);font-weight:700}}.date-block strong{{display:block;margin-top:3px;color:var(--navy);font-size:20px;line-height:1.15}}
.rail{{position:relative}}.rail:before{{content:"";position:absolute;top:0;bottom:-18px;left:33px;width:2px;background:var(--line)}}.rail i{{position:absolute;z-index:1;top:17px;left:26px;width:16px;height:16px;border:4px solid var(--ground);border-radius:50%;background:var(--accent);box-shadow:0 0 0 2px var(--line)}}
.event section{{padding:20px 24px 18px;background:#fff;border:1px solid #d4dde2;border-left:5px solid var(--accent)}}.event-top{{display:flex;align-items:center;gap:8px;font-size:11px}}.event-id{{font-weight:800;color:var(--navy)}}.tone,.precision{{padding:4px 7px;background:#edf3f4;color:#425761;font-weight:700}}.precision{{background:#f3f0e8;color:#735824}}
.event h2{{margin:10px 0 14px;color:var(--ink);font-size:19px;line-height:1.55}}
dl{{display:grid;grid-template-columns:1fr 1fr;gap:8px 22px;margin:0 0 13px}}dl div{{display:grid;grid-template-columns:76px 1fr;gap:8px}}dt,.evidence>b,.source>b,.check>b{{color:#687883;font-size:11px;font-weight:700}}dd{{margin:0;font-size:12px;line-height:1.6}}
.evidence{{display:grid;grid-template-columns:76px 1fr;gap:8px;align-items:start;margin:8px 0}}.material-id{{display:inline-block;margin:0 5px 5px 0;padding:3px 6px;border:1px solid #c7d2d8;background:#f7f9fa;color:#40535f;font:700 10px Arial}}
.source,.check{{display:grid;grid-template-columns:76px 1fr;gap:8px;margin:7px 0;font-size:12px;line-height:1.6}}.check{{padding-top:9px;border-top:1px solid #ead9d9;color:#8e3030}}.check b{{color:var(--red)}}
details{{margin-top:9px;color:#53646f;font-size:11px}}summary{{cursor:pointer;font-weight:700}}.attachments{{display:grid;grid-template-columns:1fr 1fr;gap:4px 18px;margin:9px 0 0;padding-left:18px}}a{{color:#145f79;text-decoration:none;overflow-wrap:anywhere}}.print-paths{{display:none}}
.footer{{margin:34px 0 0 248px;padding:18px 0;border-top:1px solid #b9c6cc;color:#61717b;font-size:11px;line-height:1.7}}
@media(max-width:760px){{main{{width:calc(100% - 20px);padding-top:10px}}.hero{{padding:24px 20px}}h1{{font-size:27px}}.metrics{{grid-template-columns:1fr 1fr}}.notice{{display:block}}.summary-grid{{grid-template-columns:1fr}}.summary-grid section{{padding:12px 0;border-left:0;border-top:1px solid #e1e6e9}}.event{{grid-template-columns:100px 28px 1fr}}.year-break{{margin-left:128px}}.rail:before{{left:13px}}.rail i{{left:6px}}dl{{grid-template-columns:1fr}}.attachments{{grid-template-columns:1fr}}.footer{{margin-left:128px}}}}
@media print{{@page{{size:A4;margin:13mm 11mm}}html,body{{background:#fff}}main{{width:100%;padding:0}}.hero{{padding:20px 24px 18px;-webkit-print-color-adjust:exact;print-color-adjust:exact}}h1{{font-size:25px}}.metrics{{margin-top:14px}}.metric{{padding-top:10px}}.metric b{{font-size:20px}}.notice{{display:grid;grid-template-columns:1fr auto;column-gap:28px;font-size:9px}}.notice span:last-child{{text-align:right}}.overview{{margin:14px 0 20px;padding:16px 20px}}.summary-grid p{{font-size:9px;line-height:1.45}}.timeline{{padding-top:1px}}.year-break{{margin-top:18px;margin-bottom:10px;break-after:avoid}}.event{{grid-template-columns:108px 36px 1fr;margin-bottom:9px;break-inside:avoid;page-break-inside:avoid}}.date-block{{padding:8px}}.date-block strong{{font-size:14px}}.rail:before{{left:17px;bottom:-9px}}.rail i{{top:11px;left:11px;width:13px;height:13px}}.event section{{padding:12px 15px 10px}}.event h2{{font-size:13px;margin:6px 0 8px}}dl{{margin-bottom:6px}}dd,.source,.check{{font-size:9px}}.evidence{{margin:4px 0}}details{{display:none}}.print-paths{{display:grid;grid-template-columns:76px 1fr;gap:8px;margin:5px 0 0;font-size:8px;line-height:1.45;color:#53646f;overflow-wrap:anywhere}}.print-paths b{{color:#687883;font-size:8px}}.footer{{display:none}}}}
</style></head>
<body><main>
<header class="hero"><p class="eyebrow">LEGAL AI · MATERIAL-BASED TIMELINE</p><h1>{esc(args.title)}</h1><p class="subtitle">{esc(args.subtitle)}</p>
<div class="metrics"><div class="metric"><b>{len(events)}</b><span>合并事件</span></div><div class="metric"><b>{len(material_names)}</b><span>关联材料</span></div><div class="metric"><b>{len(known_years)}</b><span>涉及年度</span></div><div class="metric"><b>{issue_count}</b><span>问题与待补材料</span></div></div>
<div class="notice"><span>时间跨度：{first_date} — {last_date}{esc(undated_note)}</span><span>{esc(args.notice)}</span></div></header>
<section class="overview"><div class="section-title"><h2>案件概览</h2><p>起因—过程—争议—现状—缺口</p></div><div class="summary-grid">{summary_html}</div></section>
<div class="legend"><span>时间与事件</span><span class="l3">相关人员/公司</span><span class="l4">相关材料</span><span class="l5">待确认事项</span></div>
<div class="timeline">{"".join(cards)}</div>
<footer class="footer">本时间轴仅依据已归档材料整理，不构成事实认定或法律结论。音视频未转写，低置信 OCR 与主体、日期、金额冲突均应回查原件。</footer>
</main></body></html>'''
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document, encoding="utf-8")
    print(args.out.resolve())


if __name__ == "__main__":
    main()

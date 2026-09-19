#!/usr/bin/env python3
"""Render the confirmed Excel timeline as deterministic HTML."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from openpyxl import load_workbook


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def main() -> None:
    parser = argparse.ArgumentParser(description="从案件材料汇总.xlsx生成时间轴HTML")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--out", type=Path, default=Path("时间轴.html"))
    args = parser.parse_args()
    wb = load_workbook(args.workbook, data_only=True, read_only=True)
    ws = wb["时间轴"]
    headers = [cell.value for cell in ws[3]]
    events = []
    for values in ws.iter_rows(min_row=4, values_only=True):
        if not any(value is not None for value in values):
            continue
        event = dict(zip(headers, values))
        if str(event.get("事件编号", "")).startswith("示例"):
            continue
        events.append(event)
    events.sort(key=lambda e: (str(e.get("事件发生时间") or "9999"), str(e.get("事件编号") or "")))
    cards = []
    for event in events:
        cards.append(f'''<article><div class="date">{esc(event.get("事件发生时间") or "时间待核")}</div><div class="dot"></div><section><small>{esc(event.get("事件编号"))} · {esc(event.get("记载性质"))}</small><h2>{esc(event.get("事件描述"))}</h2><p><b>主体：</b>{esc(event.get("涉及主体"))}</p><p><b>材料：</b>{esc(event.get("全部关联材料编号"))}</p><p class="check"><b>待核：</b>{esc(event.get("冲突/待核"))}</p></section></article>''')
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>案件材料时间轴</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f7f9;color:#17212b;font-family:Arial,"PingFang SC",sans-serif}}main{{max-width:1120px;margin:auto;padding:64px 36px}}header{{border-bottom:5px solid #17324d;padding-bottom:24px}}h1{{margin:0;color:#17324d}}.meta{{color:#66717d}}.timeline{{position:relative;margin-top:38px}}.timeline:before{{content:"";position:absolute;left:180px;top:0;bottom:0;width:3px;background:#b8c9d2}}article{{display:grid;grid-template-columns:150px 60px 1fr;align-items:start;margin:0 0 28px}}.date{{padding:10px 12px;border-radius:4px;background:#126772;color:white;font-weight:700;text-align:center}}.dot{{z-index:1;width:18px;height:18px;margin:11px auto;border:4px solid white;border-radius:50%;background:#167d86;box-shadow:0 0 0 2px #9eb2c0}}section{{padding:22px 26px;border:1px solid #d8e0e7;border-left:6px solid #167d86;border-radius:6px;background:white}}small{{color:#66717d}}h2{{margin:10px 0 14px;color:#17324d;font-size:21px}}p{{margin:6px 0}}.check{{color:#c44343}}@media(max-width:700px){{main{{padding:28px 14px}}.timeline:before{{left:42px}}article{{grid-template-columns:84px 1fr}}.date{{font-size:12px}}.dot{{display:none}}section{{grid-column:2}}}}
</style></head><body><main><header><h1>案件材料时间轴</h1><p class="meta">基于已确认事件生成，共 {len(events)} 个节点</p></header><div class="timeline">{"".join(cards)}</div></main></body></html>'''
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document, encoding="utf-8")
    print(args.out.resolve())


if __name__ == "__main__":
    main()

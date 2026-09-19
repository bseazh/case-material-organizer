#!/usr/bin/env python3
"""Generate index.txt, 002/index.md and the standard summary workbook."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "案件材料汇总模板.xlsx"


def clear_examples(ws) -> None:
    if ws.max_row >= 4:
        ws.delete_rows(4, ws.max_row - 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="根据已执行归档方案生成索引和汇总表")
    parser.add_argument("applied_plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.applied_plan.read_text(encoding="utf-8"))
    if not plan.get("confirmed") or not plan.get("result_folder"):
        raise SystemExit("需要 apply_plan.py 生成的已确认方案")
    result = Path(plan["result_folder"])
    items = plan["items"]
    summary = plan.get("case_summary") or {}

    counts = Counter(item["target_category"] for item in items)
    parse_counts = Counter(item["parse_status"] for item in items)
    lines = ["案件材料整理报告", "", "一、案件链路摘要"]
    for key in ("起因", "过程", "争议", "现状", "缺口"):
        lines.append(f"{key}：{summary.get(key, '待根据合并后的事件补充')}" )
    lines.extend(["", "二、数量统计", f"文件总数：{len(items)}"])
    lines.extend(f"{key}：{value}" for key, value in sorted(counts.items()))
    lines.extend(f"{key}：{value}" for key, value in sorted(parse_counts.items()))
    lines.extend(["", "三、文件映射"])
    for item in items:
        lines.extend([
            f"[{item['material_id']}]",
            f"原文件名：{item['original_name']}",
            f"原路径：{item['original_relative_path']}",
            f"标准文件名：{Path(item['actual_target_relative_path']).name}",
            f"归档路径：{item['actual_target_relative_path']}",
            f"状态：{item.get('apply_status', '待核')}；{item.get('parse_status', '')}", "",
        ])
    (result / "index.txt").write_text("\n".join(lines), encoding="utf-8")

    basics = sorted((x for x in items if x["target_category"] == "002 基础资料"), key=lambda x: (x["proposed_name"].startswith("时间待核"), x["proposed_name"]))
    md = ["# 基础资料索引", "", f"共 {len(basics)} 个文件。", "", "| 日期 | 材料名称 | 相对路径 | 材料编号 | 对应时间轴事项 |", "|---|---|---|---|---|"]
    for item in basics:
        date = item["proposed_name"].split("-", 1)[0]
        md.append(f"| {date} | {Path(item['actual_target_relative_path']).name} | {item['actual_target_relative_path']} | {item['material_id']} | 待事件合并后填写 |")
    (result / "002 基础资料" / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    output = result / "案件材料汇总.xlsx"
    shutil.copy2(TEMPLATE, output)
    wb = load_workbook(output)
    for ws in wb.worksheets:
        clear_examples(ws)
    overview = wb["案件链路总览"]
    for row, key in enumerate(("起因", "过程", "争议", "现状", "缺口"), 4):
        overview.cell(row, 1, key)
        overview.cell(row, 2, summary.get(key, "待根据合并后的事件补充"))
        overview.cell(row, 3, summary.get(f"{key}依据", "待补充事件编号和材料编号"))
    files = wb["文件清单"]
    for row, item in enumerate(items, 4):
        values = [item["material_id"], item["original_name"], item["original_relative_path"], Path(item["actual_target_relative_path"]).name, item["actual_target_relative_path"], item["extension"], item["sha256"], item["parse_status"], item.get("duplicate_group", ""), item.get("version_group", ""), item.get("review_notes", "")]
        for col, value in enumerate(values, 1):
            files.cell(row, col, value)
    media = wb["音视频核对"]
    media_rows = [x for x in items if "媒体" in x.get("parse_status", "")]
    for row, item in enumerate(media_rows, 4):
        values = [item["material_id"], item["original_name"], "", "当前版本不处理", "否", "仅登记和归档"]
        for col, value in enumerate(values, 1):
            media.cell(row, col, value)
    entities = wb["主体信息"]
    entity_fields = ["entity_id", "standard_name", "entity_type", "aliases", "case_roles", "strong_identifier_summary", "source_material_ids", "source_location", "confidence", "issues"]
    for row, entity in enumerate(plan.get("entities", []), 4):
        for col, field in enumerate(entity_fields, 1):
            entities.cell(row, col, entity.get(field, ""))
    timeline = wb["时间轴"]
    event_fields = ["event_id", "event_time", "material_time", "time_precision", "place_channel", "subjects", "description", "primary_material_id", "all_material_ids", "source_location", "archive_paths", "record_type", "conflicts"]
    for row, event in enumerate(plan.get("events", []), 4):
        for col, field in enumerate(event_fields, 1):
            timeline.cell(row, col, event.get(field, ""))
    issues = wb["冲突与待核"]
    issue_fields = ["issue_id", "issue", "event_ids", "material_ids", "impact", "recommended_action", "status"]
    for row, issue in enumerate(plan.get("issues", []), 4):
        for col, field in enumerate(issue_fields, 1):
            issues.cell(row, col, issue.get(field, ""))
    for ws in wb.worksheets:
        for row in ws.iter_rows(min_row=4):
            for cell in row:
                cell.font = Font(name="Arial", size=10)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
    wb.save(output)
    print(json.dumps({"result": str(result), "excel": str(output), "files": len(items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

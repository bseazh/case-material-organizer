#!/usr/bin/env python3
"""Generate index.txt, 002/index.md and the standard summary workbook."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font

from build_tree import render_tree_markdown

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "案件材料汇总模板.xlsx"


def clear_examples(ws) -> None:
    if ws.max_row >= 4:
        ws.delete_rows(4, ws.max_row - 3)


def material_ids(value: object) -> list[str]:
    """Return normalized material IDs from either a string or a list."""
    if isinstance(value, list):
        return [str(item) for item in value if re.fullmatch(r"MAT-\d{4}", str(item))]
    return re.findall(r"MAT-\d{4}", str(value or ""))


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
    media_rows = [x for x in items if x.get("parse_status") == "当前版本不处理"]
    ocr_count = sum("OCR" in x.get("parse_status", "") for x in items)
    failure_count = sum(any(word in x.get("parse_status", "") for word in ("失败", "错误")) for x in items)
    duplicate_groups = {x.get("duplicate_group") for x in items if x.get("duplicate_group")}
    duplicate_copies = sum(bool(x.get("duplicate_group")) for x in items) - len(duplicate_groups)
    event_by_material: dict[str, list[str]] = {}
    for event in plan.get("events", []):
        label = f"{event.get('event_id', '')} {event.get('description', '')}".strip()
        for material_id in material_ids(event.get("all_material_ids")):
            event_by_material.setdefault(material_id, []).append(label)

    lines = ["案件材料整理报告", "", "一、案件链路摘要"]
    for key in ("起因", "过程", "争议", "现状", "缺口"):
        lines.append(f"{key}：{summary.get(key, '待根据合并后的事件补充')}" )
    lines.extend([
        "", "二、数量统计", f"文件总数：{len(items)}",
        f"可解析数：{len(items) - len(media_rows) - failure_count}",
        f"OCR数：{ocr_count}", f"媒体数：{len(media_rows)}",
        "已匹配逐字稿数：0", f"待补逐字稿数：{len(media_rows)}",
        f"重复件：{len(duplicate_groups)}组，另有{duplicate_copies}份重复副本",
        f"解析失败数：{failure_count}",
    ])
    lines.extend(f"{key}：{value}" for key, value in sorted(counts.items()))
    lines.extend(f"{key}：{value}" for key, value in sorted(parse_counts.items()))
    lines.extend(["", "三、异常、冲突与待核"])
    for issue in plan.get("issues", []):
        lines.extend([
            f"[{issue.get('issue_id', '待编号')}] {issue.get('issue', '')}",
            f"涉及事件：{issue.get('event_ids', '')}；涉及材料：{issue.get('material_ids', '')}",
            f"影响：{issue.get('impact', '')}",
            f"建议：{issue.get('recommended_action', '')}；状态：{issue.get('status', '')}", "",
        ])
    lines.extend(["四、文件映射"])
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
        linked_events = "<br>".join(event_by_material.get(item["material_id"], ["未纳入合并事件，仅作材料索引"]))
        md.append(f"| {date} | {Path(item['actual_target_relative_path']).name} | {item['actual_target_relative_path']} | {item['material_id']} | {linked_events} |")
    (result / "002 基础资料" / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (result / "归档结果目录.md").write_text(render_tree_markdown(plan, "result"), encoding="utf-8")

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
    for row, item in enumerate(media_rows, 4):
        values = [item["material_id"], item["original_name"], "", "未匹配", "否", "当前版本不处理；仅登记和归档，待用户补充同名逐字稿"]
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
        ws.auto_filter.ref = f"A3:{get_column_letter(ws.max_column)}{max(ws.max_row, 3)}"
    wb.save(output)
    print(json.dumps({
        "result": str(result),
        "excel": str(output),
        "tree": str(result / "归档结果目录.md"),
        "files": len(items),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

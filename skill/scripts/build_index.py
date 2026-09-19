#!/usr/bin/env python3
"""Generate technical indexes plus a plain-language, user-facing workbook."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from build_tree import render_tree_markdown

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "案件材料汇总模板.xlsx"


def clear_examples(ws) -> None:
    if ws.max_row >= 4:
        ws.delete_rows(4, ws.max_row - 3)


def material_ids(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if re.fullmatch(r"MAT-\d{4}", str(item))]
    return re.findall(r"MAT-\d{4}", str(value or ""))


def clean_user_text(value: object) -> str:
    """Remove internal IDs from prose shown to non-technical users."""
    text = str(value or "").strip()
    text = re.sub(r"(?:EVT|MAT|ENT|PER|ISS)-\d{3,4}(?:\s*[、；;,至-]\s*(?:(?:EVT|MAT|ENT|PER|ISS)-)?\d{3,4})*", "", text)
    text = re.sub(r"（\s*[、；;,。\s]*）", "", text)
    text = re.sub(r"\(\s*[、；;,。\s]*\)", "", text)
    text = re.sub(r"[；;][ \t]*[；;]", "；", text)
    text = re.sub(r"[、,][ \t]*[、,]", "、", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ；;、,")


def readable_date(name: str) -> str:
    match = re.match(r"^(\d{6})(?:-(\d{6}))?-", name)
    if match:
        def expand(token: str) -> str:
            return f"20{token[:2]}-{token[2:4]}-{token[4:6]}"
        first = expand(match.group(1))
        return f"{first} 至 {expand(match.group(2))}" if match.group(2) else first
    match = re.match(r"^(\d{4})-", name)
    if match:
        token = match.group(1)
        return f"20{token[:2]}-{token[2:4]}"
    return "时间待确认"


def event_sort_key(event: dict) -> tuple[bool, str]:
    value = str(event.get("event_time") or "")
    return (re.search(r"(?:19|20)\d{2}", value) is None, value)


def material_type(item: dict) -> str:
    name = item.get("proposed_name", "")
    category = item.get("target_category", "")
    if category == "001 主体信息":
        return "主体/工商材料"
    if category == "003 委托材料":
        return "委托材料"
    if category == "004 类案及法律检索":
        return "法律检索"
    if category == "005 法律文书":
        return "法律文书"
    for keyword, label in (
        ("合同", "合同"), ("协议", "协议"), ("转账", "转账记录"),
        ("银行", "银行记录"), ("聊天", "聊天记录"), ("检测报告", "检测报告"),
        ("录音", "录音"), ("逐字稿", "逐字稿"), ("照片", "图片/照片"),
    ):
        if keyword in name:
            return label
    return {
        ".pdf": "PDF文档", ".doc": "Word文档", ".docx": "Word文档",
        ".xls": "Excel表格", ".xlsx": "Excel表格", ".csv": "表格数据",
        ".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".txt": "文本材料",
        ".m4a": "录音", ".mp3": "录音", ".wav": "录音", ".mp4": "视频", ".mov": "视频",
    }.get(str(item.get("extension", "")).lower(), "其他材料")


def friendly_status(item: dict, has_transcript: bool = False) -> str:
    status = str(item.get("parse_status", ""))
    if status == "当前版本不处理":
        return "已找到候选逐字稿" if has_transcript else "未解析，待提供逐字稿"
    if "OCR低置信" in status:
        return "已识别，需核对原件"
    if "失败" in status or "错误" in status:
        return "读取失败，需人工检查"
    if status:
        return "已读取"
    return "待确认"


def transcript_matches(items: list[dict]) -> dict[str, dict]:
    text_extensions = {".doc", ".docx", ".txt", ".pdf"}
    text_items = [x for x in items if str(x.get("extension", "")).lower() in text_extensions]
    matches: dict[str, dict] = {}
    for media in (x for x in items if x.get("parse_status") == "当前版本不处理"):
        tokens = set(re.findall(r"\d{8,14}", media.get("original_name", "")))
        candidates = [item for item in text_items if tokens and tokens.intersection(re.findall(r"\d{8,14}", item.get("original_name", "")))]
        if len(candidates) == 1:
            matches[media["material_id"]] = candidates[0]
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description="根据已执行归档方案生成索引和用户版汇总表")
    parser.add_argument("applied_plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.applied_plan.read_text(encoding="utf-8"))
    if not plan.get("confirmed") or not plan.get("result_folder"):
        raise SystemExit("需要 apply_plan.py 生成的已确认方案")

    result = Path(plan["result_folder"])
    items = plan["items"]
    summary = plan.get("case_summary") or {}
    item_by_id = {item["material_id"]: item for item in items}
    events = sorted(plan.get("events", []), key=event_sort_key)
    media_matches = transcript_matches(items)
    counts = Counter(item["target_category"] for item in items)
    parse_counts = Counter(item["parse_status"] for item in items)
    media_rows = [x for x in items if x.get("parse_status") == "当前版本不处理"]
    ocr_count = sum("OCR" in x.get("parse_status", "") for x in items)
    failure_count = sum(any(word in x.get("parse_status", "") for word in ("失败", "错误")) for x in items)
    duplicate_groups = {x.get("duplicate_group") for x in items if x.get("duplicate_group")}
    duplicate_copies = sum(bool(x.get("duplicate_group")) for x in items) - len(duplicate_groups)

    event_by_material: dict[str, list[str]] = {}
    for event in events:
        description = clean_user_text(event.get("description", ""))
        for material_id in material_ids(event.get("all_material_ids")):
            event_by_material.setdefault(material_id, []).append(description)

    lines = ["案件材料整理报告", "", "一、案件链路摘要"]
    for key in ("起因", "过程", "争议", "现状", "缺口"):
        lines.append(f"{key}：{summary.get(key, '待根据合并后的事件补充')}")
    lines.extend([
        "", "二、数量统计", f"文件总数：{len(items)}",
        f"可解析数：{len(items) - len(media_rows) - failure_count}", f"OCR数：{ocr_count}",
        f"媒体数：{len(media_rows)}", f"已发现候选逐字稿数：{len(media_matches)}（仍需核验音文一致性）",
        f"待补逐字稿数：{len(media_rows) - len(media_matches)}",
        f"重复件：{len(duplicate_groups)}组，另有{duplicate_copies}份重复副本", f"解析失败数：{failure_count}",
    ])
    lines.extend(f"{key}：{value}" for key, value in sorted(counts.items()))
    lines.extend(f"{key}：{value}" for key, value in sorted(parse_counts.items()))
    lines.extend(["", "三、异常、冲突与待核"])
    for issue in plan.get("issues", []):
        lines.extend([
            f"[{issue.get('issue_id', '待编号')}] {issue.get('issue', '')}",
            f"涉及事件：{issue.get('event_ids', '')}；涉及材料：{issue.get('material_ids', '')}",
            f"影响：{issue.get('impact', '')}", f"建议：{issue.get('recommended_action', '')}；状态：{issue.get('status', '')}", "",
        ])
    lines.append("四、文件映射")
    for item in items:
        lines.extend([
            f"[{item['material_id']}]", f"原文件名：{item['original_name']}", f"原路径：{item['original_relative_path']}",
            f"标准文件名：{Path(item['actual_target_relative_path']).name}", f"归档路径：{item['actual_target_relative_path']}",
            f"状态：{item.get('apply_status', '待核')}；{item.get('parse_status', '')}", "",
        ])
    (result / "index.txt").write_text("\n".join(lines), encoding="utf-8")

    basics = sorted((x for x in items if x["target_category"] == "002 基础资料"), key=lambda x: (x["proposed_name"].startswith("时间待核"), x["proposed_name"]))
    md = ["# 基础资料索引", "", f"共 {len(basics)} 个文件。", "", "| 日期 | 材料名称 | 相对路径 | 材料编号 | 对应时间轴事项 |", "|---|---|---|---|---|"]
    for item in basics:
        linked_events = "<br>".join(event_by_material.get(item["material_id"], ["未纳入合并事件，仅作材料索引"]))
        md.append(f"| {readable_date(item['proposed_name'])} | {Path(item['actual_target_relative_path']).name} | {item['actual_target_relative_path']} | {item['material_id']} | {linked_events} |")
    (result / "002 基础资料" / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (result / "归档结果目录.md").write_text(render_tree_markdown(plan, "result"), encoding="utf-8")

    output = result / "案件材料汇总.xlsx"
    shutil.copy2(TEMPLATE, output)
    wb = load_workbook(output)
    for ws in wb.worksheets:
        clear_examples(ws)

    overview = wb["案件概览"]
    for row, key in enumerate(("起因", "过程", "争议", "现状", "缺口"), 4):
        overview.cell(row, 1, key)
        overview.cell(row, 2, clean_user_text(summary.get(key, "待补充")))

    materials = wb["材料清单"]
    for row, item in enumerate(items, 4):
        descriptions = list(dict.fromkeys(event_by_material.get(item["material_id"], [])))
        content = "；".join(descriptions) if descriptions else clean_user_text(item.get("review_notes", "未纳入时间轴，仅作材料索引。"))
        values = [readable_date(item["proposed_name"]), Path(item["actual_target_relative_path"]).name, material_type(item), content, item["target_category"], friendly_status(item, item["material_id"] in media_matches)]
        for col, value in enumerate(values, 1):
            materials.cell(row, col, value)

    parties = wb["当事人信息"]
    for row, entity in enumerate(plan.get("entities", []), 4):
        details = []
        if entity.get("entity_type"):
            details.append(f"类型：{entity['entity_type']}")
        aliases = str(entity.get("aliases", "")).strip()
        if aliases and aliases not in {"无", "-"}:
            details.append(f"其他称呼：{aliases}")
        if entity.get("confidence") and entity.get("confidence") != "高":
            details.append(f"识别状态：{entity['confidence']}置信")
        values = [entity.get("standard_name", ""), entity.get("case_roles", ""), "；".join(details) or "信息来自归档材料。", entity.get("issues", "")]
        for col, value in enumerate(values, 1):
            parties.cell(row, col, clean_user_text(value))

    media_ws = wb["音视频材料"]
    for row, item in enumerate(media_rows, 4):
        transcript = media_matches.get(item["material_id"])
        transcript_name = Path(transcript["actual_target_relative_path"]).name if transcript else "未找到"
        handling = "已找到候选逐字稿" if transcript else "待补充逐字稿"
        note = "音视频未播放、未转写；仅分析逐字稿，两者内容是否一致仍需人工确认。" if transcript else "音视频未播放、未转写，也未纳入事实分析。"
        for col, value in enumerate([Path(item["actual_target_relative_path"]).name, transcript_name, handling, note], 1):
            media_ws.cell(row, col, value)

    timeline = wb["案件时间轴"]
    for row, event in enumerate(events, 4):
        linked_names = []
        for material_id in material_ids(event.get("all_material_ids")):
            item = item_by_id.get(material_id)
            if item:
                linked_names.append(Path(item["actual_target_relative_path"]).name)
        values = [event.get("event_time", "时间待确认"), clean_user_text(event.get("description", "")), clean_user_text(event.get("subjects", "")), "；".join(linked_names), clean_user_text(event.get("conflicts", "无"))]
        for col, value in enumerate(values, 1):
            timeline.cell(row, col, value)

    issues = wb["问题与待补材料"]
    for row, issue in enumerate(plan.get("issues", []), 4):
        values = [issue.get("issue", ""), issue.get("impact", ""), issue.get("recommended_action", ""), issue.get("status", "")]
        for col, value in enumerate(values, 1):
            issues.cell(row, col, clean_user_text(value))

    for ws in wb.worksheets:
        for data_row in ws.iter_rows(min_row=4):
            for cell in data_row:
                cell.font = Font(name="Arial", size=10)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        ws.auto_filter.ref = f"A3:{get_column_letter(ws.max_column)}{max(ws.max_row, 3)}"
        ws.freeze_panes = "A4"
    wb.save(output)
    print(json.dumps({"result": str(result), "excel": str(output), "tree": str(result / '归档结果目录.md'), "files": len(items)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

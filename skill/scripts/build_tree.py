#!/usr/bin/env python3
"""Build a Markdown directory-tree confirmation from a preview or applied plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FOLDERS = ["001 主体信息", "002 基础资料", "003 委托材料", "004 类案及法律检索", "005 法律文书"]
OUTPUT_FOLDER = "整理结果"
TECH_FOLDER = "技术资料"


def md_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br>")


def display_name(item: dict, stage: str) -> str:
    if stage == "result" and item.get("actual_target_relative_path"):
        return Path(item["actual_target_relative_path"]).name
    return item["proposed_name"]


def sort_key(item: dict, stage: str) -> tuple[bool, str, str]:
    name = display_name(item, stage)
    return (name.startswith("时间待核-"), name.casefold(), item.get("material_id", ""))


def tree_lines(plan: dict, stage: str) -> list[str]:
    items = plan.get("items", [])
    result_name = (
        Path(plan.get("result_folder", "")).name
        if stage == "result" and plan.get("result_folder")
        else f"{Path(plan['source_folder']).name}_整理结果"
    )
    grouped = {folder: [] for folder in FOLDERS}
    for item in items:
        folder = item.get("target_category")
        if folder not in grouped:
            raise ValueError(f"不支持的一级目录：{folder}")
        grouped[folder].append(item)

    lines = [f"{result_name}/"]
    for folder in FOLDERS:
        folder_branch = "├──" if stage == "result" else ("└──" if folder == FOLDERS[-1] else "├──")
        folder_items = sorted(grouped[folder], key=lambda item: sort_key(item, stage))
        unit = "份材料" if stage == "result" else "个文件"
        lines.append(f"{folder_branch} {folder}/（{len(folder_items)} {unit}）")
        prefix = "│   " if stage == "result" or folder != FOLDERS[-1] else "    "
        has_basic_index = (
            stage == "result"
            and folder == "002 基础资料"
            and (Path(plan["result_folder"]) / folder / "index.md").exists()
        )
        if not folder_items:
            lines.append(f"{prefix}└── 本次未发现相关材料")
            continue
        for item_index, item in enumerate(folder_items):
            file_branch = "└──" if item_index == len(folder_items) - 1 and not has_basic_index else "├──"
            lines.append(f"{prefix}{file_branch} {display_name(item, stage)}")
        if has_basic_index:
            lines.append(f"{prefix}└── index.md（基础资料索引）")
    if stage == "result":
        result_root = Path(plan["result_folder"])
        output = result_root / OUTPUT_FOLDER
        visible = sorted((p for p in output.iterdir() if not p.name.startswith(".")), key=lambda p: (p.is_dir(), p.name.casefold())) if output.exists() else []
        lines.append(f"└── {OUTPUT_FOLDER}/（{sum(p.is_file() for p in visible)} 个成果文件）")
        for index, path in enumerate(visible):
            branch = "└──" if index == len(visible) - 1 else "├──"
            lines.append(f"    {branch} {path.name}{'/' if path.is_dir() else ''}")
            if path.is_dir():
                children = sorted((p for p in path.iterdir() if not p.name.startswith(".")), key=lambda p: p.name.casefold())
                child_prefix = "        " if index == len(visible) - 1 else "    │   "
                for child_index, child in enumerate(children):
                    child_branch = "└──" if child_index == len(children) - 1 else "├──"
                    lines.append(f"{child_prefix}{child_branch} {child.name}")
    return lines


def parse_totals(items: list[dict]) -> tuple[int, int]:
    unparsed = sum(
        item.get("parse_status") == "当前版本不处理"
        or any(word in str(item.get("parse_status", "")) for word in ("失败", "错误"))
        for item in items
    )
    return len(items) - unparsed, unparsed


def render_tree_markdown(plan: dict, stage: str) -> str:
    items = plan.get("items", [])
    if stage == "result" and not plan.get("confirmed"):
        raise ValueError("结果目录树只能根据已确认并执行的方案生成")
    parsed_count, unparsed_count = parse_totals(items)
    title = "归档结果目录" if stage == "result" else "拟归档目录预览"
    status = "已执行，以实际归档路径为准" if stage == "result" else "待用户确认，尚未复制文件"
    if stage == "result":
        timeline_exists = (Path(plan["result_folder"]) / OUTPUT_FOLDER / "案件材料时间轴.html").exists()
        timeline_action = "A. 重新生成或更新时间轴 HTML/PNG/PDF" if timeline_exists else "A. 生成案件时间轴 HTML/PNG/PDF"
        options = [timeline_action, "B. 只保留 Excel、TXT 和归档目录", "C. 先打开或检查整理结果"]
    else:
        options = ["A. 确认目录与命名，执行归档", "B. 调整分类、命名或事件合并方案", "C. 只保留预览，不复制文件"]
    lines = [
        f"# {title}", "",
        f"- 原始目录：`{plan.get('source_folder', '')}`",
        f"- 当前状态：{status}",
        f"- 文件总数：{len(items)}",
        f"- 成功解析：{parsed_count}",
        f"- 未解析：{unparsed_count}", "", "## 目录树", "", "```text",
        *tree_lines(plan, stage), "```",
    ]
    if stage == "preview":
        lines.extend(["", "## 文件改名确认", "", "| 原文件名 | 改名后文件名 | 目标目录 |", "|---|---|---|"])
        for item in sorted(items, key=lambda row: (FOLDERS.index(row["target_category"]), sort_key(row, stage))):
            lines.append(
                f"| {md_cell(item.get('original_name'))} | {md_cell(display_name(item, stage))} | "
                f"{md_cell(item.get('target_category'))} |"
            )
    lines.extend(["", "## 下一步", "", *options, ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成归档前/后的 Markdown 目录树交互文件")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--stage", choices=("preview", "result"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stdout", action="store_true", help="将完整 Markdown 同时输出到终端")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    document = render_tree_markdown(plan, args.stage)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(document, encoding="utf-8")
    if args.stdout:
        print(document)
    else:
        print(json.dumps({"output": str(args.out.resolve()), "stage": args.stage, "items": len(plan.get("items", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

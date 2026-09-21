#!/usr/bin/env python3
"""Build a Markdown directory-tree confirmation from a preview or applied plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from case_naming import case_folder_name, directory_structure, directory_subfolders, item_target_directory

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
    result_name = case_folder_name(plan)
    folders = directory_structure(plan)
    subfolders = directory_subfolders(plan, folders)
    if stage == "result" and Path(plan.get("result_folder", "")).name != result_name:
        raise ValueError(f"实际结果文件夹名称不符合规则，应为：{result_name}")
    grouped = {folder: [] for folder in folders}
    for item in items:
        item_target_directory(plan, item)
        folder = item["target_category"]
        grouped[folder].append(item)

    lines = [f"{result_name}/"]
    for folder_index, folder in enumerate(folders):
        top_is_last = stage != "result" and folder_index == len(folders) - 1
        folder_branch = "└──" if top_is_last else "├──"
        folder_items = sorted(grouped[folder], key=lambda item: sort_key(item, stage))
        unit = "份材料" if stage == "result" else "个文件"
        lines.append(f"{folder_branch} {folder}/（{len(folder_items)} {unit}）")
        prefix = "    " if top_is_last else "│   "
        has_basic_index = (
            stage == "result"
            and folder == "002 基础资料"
            and (Path(plan["result_folder"]) / folder / "index.md").exists()
        )
        declared_children = subfolders[folder]
        direct_items = [item for item in folder_items if not item.get("target_subcategory")]
        child_items = {
            child: [item for item in folder_items if item.get("target_subcategory") == child]
            for child in declared_children
        }
        entries: list[tuple[str, object]] = [("file", item) for item in direct_items]
        entries.extend(("folder", child) for child in declared_children)
        if has_basic_index:
            entries.append(("index", "index.md（基础资料索引）"))
        if not entries:
            lines.append(f"{prefix}└── 本次未发现相关材料")
            continue
        for entry_index, (kind, value) in enumerate(entries):
            entry_is_last = entry_index == len(entries) - 1
            branch = "└──" if entry_is_last else "├──"
            if kind == "file":
                lines.append(f"{prefix}{branch} {display_name(value, stage)}")
            elif kind == "index":
                lines.append(f"{prefix}{branch} {value}")
            else:
                children = sorted(child_items[str(value)], key=lambda item: sort_key(item, stage))
                lines.append(f"{prefix}{branch} {value}/（{len(children)} {unit}）")
                nested_prefix = prefix + ("    " if entry_is_last else "│   ")
                if not children:
                    lines.append(f"{nested_prefix}└── 本次未发现相关材料")
                for child_index, item in enumerate(children):
                    child_branch = "└──" if child_index == len(children) - 1 else "├──"
                    lines.append(f"{nested_prefix}{child_branch} {display_name(item, stage)}")
    if stage == "result":
        result_root = Path(plan["result_folder"])
        output = result_root / OUTPUT_FOLDER
        visible = sorted((p for p in output.iterdir() if not p.name.startswith(".")), key=lambda p: (p.is_dir(), p.name.casefold())) if output.exists() else []
        lines.append(f"└── {OUTPUT_FOLDER}/（{sum(p.is_file() for p in visible)} 个成果文件）")
        for index, path in enumerate(visible):
            branch = "└──" if index == len(visible) - 1 else "├──"
            lines.append(f"    {branch} {path.name}{'/' if path.is_dir() else ''}")
            if path.is_dir() and path.name != TECH_FOLDER:
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
    folders = directory_structure(plan)
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
        *([f"- 结果位置：`{Path(plan['result_folder']).resolve()}`"] if stage == "result" else []),
        f"- 当前状态：{status}",
        f"- 材料总数：{len(items)}",
        f"- 已整理材料：{parsed_count}",
        f"- 需人工查看：{unparsed_count}", "", "## 目录树", "", "```text",
        *tree_lines(plan, stage), "```",
    ]
    if stage == "preview":
        lines.extend(["", "## 文件改名确认", "", "| 原文件名 | 改名后文件名 | 目标目录 |", "|---|---|---|"])
        for item in sorted(items, key=lambda row: (folders.index(row["target_category"]), item_target_directory(plan, row).as_posix(), sort_key(row, stage))):
            lines.append(
                f"| {md_cell(item.get('original_name'))} | {md_cell(display_name(item, stage))} | "
                f"{md_cell(item_target_directory(plan, item).as_posix())} |"
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

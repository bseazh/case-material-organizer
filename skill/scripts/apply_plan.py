#!/usr/bin/env python3
"""Apply an explicitly confirmed plan by copying files into five folders."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

FOLDERS = ["001 主体信息", "002 基础资料", "003 委托材料", "004 类案及法律检索", "005 法律文书"]
OUTPUT_FOLDER = "整理结果"
TECH_FOLDER = "技术资料"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for number in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{number:02d}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"无法生成唯一文件名：{path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="按已确认方案复制归档")
    parser.add_argument("plan", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("--confirmed", action="store_true", help="确认已由用户审核方案")
    args = parser.parse_args()
    if not args.confirmed:
        raise SystemExit("未执行：必须在用户确认方案后提供 --confirmed")
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    source, result = Path(plan["source_folder"]).resolve(), args.result.resolve()
    if result == source or source in result.parents:
        raise SystemExit("结果目录不得等于或位于原始材料目录内部")
    result.mkdir(parents=True, exist_ok=True)
    for folder in FOLDERS:
        (result / folder).mkdir(exist_ok=True)
    technical = result / OUTPUT_FOLDER / TECH_FOLDER
    technical.mkdir(parents=True, exist_ok=True)

    copied = 0
    for item in plan["items"]:
        src = source / item["original_relative_path"]
        dst = unique_path(result / item["target_category"] / item["proposed_name"])
        shutil.copy2(src, dst)
        item["actual_target_relative_path"] = dst.relative_to(result).as_posix()
        item["apply_status"] = "已复制"
        copied += 1
    for folder in FOLDERS:
        target = result / folder
        if not any(target.iterdir()):
            (target / "README_本次未发现相关材料.txt").write_text("本次整理未发现可归入本目录的材料。\n", encoding="utf-8")
    applied = technical / "归档方案_已执行.json"
    plan["confirmed"], plan["result_folder"] = True, str(result)
    applied.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(result), "copied": copied, "applied_plan": str(applied)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

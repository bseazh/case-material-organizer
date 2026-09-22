#!/usr/bin/env python3
"""Rebuild searchable extraction files for every archived material before report retry."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="为报告缺项补充扫描准备全部材料文本")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    items = plan.get("items") if isinstance(plan.get("items"), list) else []
    if not items:
        raise SystemExit("归档方案没有材料，无法重新扫描")

    result_folder = Path(str(plan.get("result_folder") or ""))
    archived_ready = result_folder.is_dir() and all(
        str(item.get("actual_target_relative_path") or "").strip()
        and (result_folder / str(item.get("actual_target_relative_path"))).is_file()
        for item in items if isinstance(item, dict)
    )
    if archived_ready:
        source_folder = result_folder
        files = [{**item, "original_relative_path": item["actual_target_relative_path"]} for item in items]
        source_kind = "archived_copies"
    else:
        source_folder = Path(str(plan.get("source_folder") or ""))
        if not source_folder.is_dir():
            raise SystemExit("原材料和归档副本均不可访问，无法重新扫描")
        files = items
        source_kind = "original_sources"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = args.out_dir / "rescan-inventory.json"
    inventory_path.write_text(json.dumps({
        "schema_version": "1.0",
        "source_folder": str(source_folder.resolve()),
        "file_count": len(files),
        "files": files,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    extraction_dir = args.out_dir / "content"
    subprocess.run([
        sys.executable,
        str(Path(__file__).with_name("extract_content.py")),
        str(inventory_path),
        "--out-dir", str(extraction_dir),
    ], check=True)

    state = plan.setdefault("rescan_state", {})
    state["attempts"] = int(state.get("attempts") or 0) + 1
    state["last_attempt_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    state["source_kind"] = source_kind
    state["inventory_path"] = str(inventory_path.resolve())
    state["extractions_path"] = str((extraction_dir / "extractions.json").resolve())
    args.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

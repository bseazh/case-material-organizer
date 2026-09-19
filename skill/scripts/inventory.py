#!/usr/bin/env python3
"""Create a read-only inventory for one supplied case-material folder."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

MEDIA = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".mp4", ".mov", ".avi", ".mkv"}
SUPPORTED = {".pdf", ".docx", ".xlsx", ".xlsm", ".csv", ".tsv", ".txt", ".md", ".json", ".png", ".jpg", ".jpeg", ".webp"}
SYSTEM_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="只读清点案件材料文件夹")
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, default=Path("inventory.json"))
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.is_dir():
        raise SystemExit(f"输入不是可读取文件夹：{source}")

    rows, skipped = [], []
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        if path.name in SYSTEM_FILES or path.name.startswith("._"):
            skipped.append(path.relative_to(source).as_posix())
            continue
        stat = path.stat()
        suffix = path.suffix.lower()
        rows.append({
            "original_name": path.name,
            "original_relative_path": path.relative_to(source).as_posix(),
            "extension": suffix,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "sha256": digest(path),
            "parse_status": "媒体仅登记-不解析" if suffix in MEDIA else ("待提取" if suffix in SUPPORTED else "当前版本不支持解析"),
        })
    payload = {"schema_version": "1.0", "source_folder": str(source), "file_count": len(rows), "skipped_system_files": skipped, "files": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.out.resolve()), "files": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

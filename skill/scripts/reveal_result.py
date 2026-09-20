#!/usr/bin/env python3
"""Reveal a completed result folder and always report its absolute path."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path


def reveal(path: Path) -> tuple[bool, str]:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", "-R", str(path)], check=True)
            return True, "访达"
        if system == "Windows":
            subprocess.run(["explorer", f"/select,{path}"], check=True)
            return True, "文件资源管理器"
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            subprocess.run(["xdg-open", str(path)], check=True)
            return True, "文件管理器"
    except (OSError, subprocess.CalledProcessError):
        pass
    return False, "文件管理器"


def main() -> None:
    parser = argparse.ArgumentParser(description="在系统文件管理器中定位整理结果")
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    result = args.result.resolve()
    if not result.is_dir():
        raise SystemExit(f"结果文件夹不存在：{result}")
    opened, manager = reveal(result)
    print(json.dumps({
        "opened": opened,
        "manager": manager,
        "absolute_path": str(result),
        "message": f"已在{manager}中为你打开整理结果文件夹" if opened else "未能自动打开文件管理器，请使用以下绝对路径",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

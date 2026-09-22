#!/usr/bin/env python3
"""Check whether a plan has enough sourced content for a non-empty report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from completeness import normalize_mode, validate_analysis_readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="检查案件报告的主体、总结、事件和事实是否齐全")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    result = validate_analysis_readiness(plan, require_report=True)
    mode = normalize_mode(plan.get("processing_mode"))
    payload = {
        "ready": result.passed,
        "processing_mode": mode,
        "rescan_required": not result.passed and mode == "full-review",
        "next_action": (
            "可生成初步报告" if result.passed and mode == "draft"
            else "按用户指定问题补充核对" if not result.passed and mode in {"draft", "focused-review"}
            else "执行一次全量补充扫描" if not result.passed
            else "可生成报告"
        ),
        "errors": list(result.errors),
        "plan": str(args.plan.resolve()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not result.passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

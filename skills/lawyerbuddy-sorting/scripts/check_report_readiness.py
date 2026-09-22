#!/usr/bin/env python3
"""Check whether a plan has enough sourced content for a non-empty report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from completeness import validate_analysis_readiness


def main() -> None:
    parser = argparse.ArgumentParser(description="检查案件报告的主体、总结、事件和事实是否齐全")
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    result = validate_analysis_readiness(plan, require_report=True)
    payload = {
        "ready": result.passed,
        "rescan_required": not result.passed,
        "errors": list(result.errors),
        "plan": str(args.plan.resolve()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not result.passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

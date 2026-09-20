#!/usr/bin/env python3
"""Validate the lawyer-facing case folder name shared by preview and apply steps."""

from __future__ import annotations

import re

INVALID = re.compile(r'[\\/:*?"<>|\r\n]')


def case_folder_name(plan: dict) -> str:
    case = plan.get("case_folder") or {}
    sequence = str(case.get("sequence", "")).strip()
    plaintiff = str(case.get("plaintiff_short_name", "")).strip()
    defendant = str(case.get("defendant_short_name", "")).strip()
    cause = str(case.get("cause_of_action", "")).strip()

    missing = [
        label for label, value in (
            ("序号", sequence),
            ("原告简称", plaintiff),
            ("被告简称", defendant),
            ("案由", cause),
        ) if not value
    ]
    if missing:
        raise ValueError(f"案件文件夹名称待确认：缺少{'、'.join(missing)}")
    if not re.fullmatch(r"[1-9]\d*", sequence):
        raise ValueError("案件文件夹序号必须是从 1 开始的正整数")
    for label, value in (("原告简称", plaintiff), ("被告简称", defendant), ("案由", cause)):
        if INVALID.search(value) or "-" in value:
            raise ValueError(f"{label}含有不能用于文件夹名称的字符")

    expected = f"{sequence}-{plaintiff}VS{defendant}-{cause}"
    if len(expected) > 120:
        raise ValueError("案件文件夹名称过长，请进一步缩短当事人简称或案由")
    recorded = str(plan.get("case_folder_name", "")).strip()
    if recorded and recorded != expected:
        raise ValueError(f"案件文件夹名称与字段不一致，应为：{expected}")
    return expected

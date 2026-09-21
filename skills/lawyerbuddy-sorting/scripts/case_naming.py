#!/usr/bin/env python3
"""Validate the lawyer-facing case folder name shared by preview and apply steps."""

from __future__ import annotations

import re
from pathlib import Path

from cause_catalog import DEFAULT_CATALOG, load_catalog

INVALID = re.compile(r'[\\/:*?"<>|\r\n]')
DEFAULT_FOLDERS = ["001 主体信息", "002 基础资料", "003 委托材料", "004 类案及法律检索", "005 法律文书"]
RESERVED_FOLDERS = {"整理结果", "技术资料", ".", ".."}


def _folder_name(value: object, label: str) -> str:
    name = str(value or "").strip()
    if not name:
        raise ValueError(f"{label}不能为空")
    if INVALID.search(name) or name in RESERVED_FOLDERS:
        raise ValueError(f"{label}含有不能用于目录名称的内容：{name}")
    if len(name) > 80:
        raise ValueError(f"{label}过长：{name}")
    return name


def directory_structure(plan: dict) -> list[str]:
    """Return and validate the confirmed top-level material folders."""
    mode = str(plan.get("directory_mode") or "legacy").strip().lower()
    recorded = plan.get("directory_structure")
    if mode in {"legacy", "default"}:
        if recorded and recorded != DEFAULT_FOLDERS:
            raise ValueError("默认目录必须严格使用 001 至 005 标准结构")
        return list(DEFAULT_FOLDERS)
    if mode != "custom":
        raise ValueError("目录方案待确认：请选择 default 或 custom")
    if not isinstance(recorded, list) or not recorded:
        raise ValueError("自定义目录不能为空")
    folders = [_folder_name(value, "自定义一级目录") for value in recorded]
    if len(folders) != len(set(folders)):
        raise ValueError("自定义一级目录不能重名")
    if len(folders) > 12:
        raise ValueError("自定义一级目录不宜超过 12 个，请合并相近分类")
    return folders


def directory_subfolders(plan: dict, folders: list[str] | None = None) -> dict[str, list[str]]:
    """Validate optional second-level folders declared by the confirmed plan."""
    folders = folders or directory_structure(plan)
    recorded = plan.get("directory_subfolders") or {}
    if not isinstance(recorded, dict):
        raise ValueError("二级目录设置必须是“一级目录：二级目录列表”的形式")
    result = {folder: [] for folder in folders}
    for parent, values in recorded.items():
        if parent not in result:
            raise ValueError(f"二级目录所属的一级目录不存在：{parent}")
        if not isinstance(values, list):
            raise ValueError(f"{parent} 的二级目录必须使用列表")
        children = [_folder_name(value, f"{parent} 的二级目录") for value in values]
        if len(children) != len(set(children)):
            raise ValueError(f"{parent} 的二级目录不能重名")
        result[parent] = children
    return result


def item_target_directory(plan: dict, item: dict) -> Path:
    folders = directory_structure(plan)
    subfolders = directory_subfolders(plan, folders)
    parent = str(item.get("target_category") or "").strip()
    if parent not in folders:
        raise ValueError(f"材料尚未归入已确认的一级目录：{item.get('original_name', '')}")
    child = str(item.get("target_subcategory") or "").strip()
    if child and child not in subfolders[parent]:
        raise ValueError(f"材料的二级目录未在方案中确认：{parent}/{child}")
    if plan.get("directory_mode") == "default" and parent == "002 基础资料" and not child:
        raise ValueError(f"基础资料尚未完成二级分类：{item.get('original_name', '')}")
    return Path(parent) / child if child else Path(parent)


def confirmed_cause(plan: dict) -> str:
    """Return the user-confirmed primary cause shared by every title."""
    review = plan.get("cause_of_action_review") or {}
    primary = str(review.get("primary_cause") or "").strip()
    status = str(review.get("status") or "").strip().lower()
    if status != "confirmed" or review.get("confirmed_by_user") is not True:
        raise ValueError("主要案由尚未由用户确认")
    if not primary:
        raise ValueError("已确认案由记录缺少主要案由")
    try:
        level = int(review.get("level"))
    except (TypeError, ValueError):
        raise ValueError("已确认案由缺少有效层级") from None
    hierarchy = [str(value).strip() for value in review.get("hierarchy") or [] if str(value).strip()]
    matches = [
        record for record in load_catalog(DEFAULT_CATALOG)
        if record["name"] == primary and record["level"] == level and record["hierarchy"] == hierarchy
    ]
    if not matches:
        raise ValueError("主要案由、层级或上级链与内置案由参考表不一致")
    cause = str((plan.get("case_folder") or {}).get("cause_of_action") or "").strip()
    if cause != primary:
        raise ValueError(f"案件文件夹案由与已确认主要案由不一致，应为：{primary}")
    return primary


def report_filename(plan: dict) -> str:
    return f"{confirmed_cause(plan)}案件梳理报告.docx"


def timeline_filename(plan: dict) -> str:
    return f"{confirmed_cause(plan)}案件关键时间轴.html"


def report_title(plan: dict) -> str:
    return f"{confirmed_cause(plan)}案件梳理报告"


def timeline_title(plan: dict) -> str:
    return f"{confirmed_cause(plan)}｜案件关键时间轴"


def case_folder_name(plan: dict) -> str:
    case = plan.get("case_folder") or {}
    sequence = str(case.get("sequence", "")).strip()
    plaintiff = str(case.get("plaintiff_short_name", "")).strip()
    defendant = str(case.get("defendant_short_name", "")).strip()
    cause = confirmed_cause(plan)

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

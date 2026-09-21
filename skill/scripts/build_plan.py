#!/usr/bin/env python3
"""Build a reviewable classification and naming plan; never copies files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from case_naming import DEFAULT_FOLDERS, directory_structure

CATEGORIES = {
    "001 主体信息": ("营业执照", "身份证", "工牌", "花名册", "主体", "工商"),
    "003 委托材料": ("委托", "授权", "律所函", "送达地址"),
    "004 类案及法律检索": ("类案", "判决", "裁定", "法规", "法条", "检索报告"),
    "005 法律文书": ("起诉状", "答辩状", "上诉状", "证据目录", "法律意见书", "律师函"),
}
BASIC_SUBCATEGORIES = (
    ("01 合同协议", ("合同", "协议", "补充协议", "订单")),
    ("02 付款凭证", ("付款", "转账", "回款", "银行", "流水", "发票", "收据", "工资", "结算", "扣款")),
    ("03 履约资料", ("交付", "验收", "发货", "物流", "施工", "工程", "进度", "工作记录")),
    ("04 质量检测与鉴定", ("质量", "检测", "检验", "鉴定", "抽检", "复检")),
    ("05 考勤社保与人事", ("考勤", "排班", "社保", "公积金", "调岗", "入职", "离职")),
    ("06 事故医疗与现场", ("事故", "工伤", "医疗", "门诊", "病历", "诊断", "现场", "设备")),
    ("07 沟通与通知", ("聊天", "微信", "沟通", "通知", "会议", "录音", "逐字稿", "函件")),
)
DATE_PATTERNS = [
    (re.compile(r"(?<!\d)(20\d{2})[-_.年](0?[1-9]|1[0-2])[-_.月](0?[1-9]|[12]\d|3[01])日?\s*(?:至|到|—|~)\s*(20\d{2})[-_.年](0?[1-9]|1[0-2])[-_.月](0?[1-9]|[12]\d|3[01])日?(?!\d)"), "range_ymd"),
    (re.compile(r"(?<!\d)(20\d{2})[-_.年](0?[1-9]|1[0-2])月?\s*(?:至|到|—|~)\s*(20\d{2})[-_.年](0?[1-9]|1[0-2])月?(?!\d)"), "range_ym"),
    (re.compile(r"(?<!\d)(20\d{2})[-_.年](0?[1-9]|1[0-2])[-_.月](0?[1-9]|[12]\d|3[01])日?(?!\d)"), "ymd"),
    (re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)"), "ymd"),
    (re.compile(r"(?<!\d)(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)"), "ymd"),
    (re.compile(r"(?<!\d)(20\d{2})[-_.年](0?[1-9]|1[0-2])月?(?!\d)"), "ym"),
    (re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)"), "ym"),
]


def category(name: str) -> str:
    for folder, words in CATEGORIES.items():
        if any(word in name for word in words):
            return folder
    return "002 基础资料"


def basic_subcategory(name: str) -> str:
    for folder, words in BASIC_SUBCATEGORIES:
        if any(word in name for word in words):
            return folder
    return "99 其他基础资料"


def date_token(name: str) -> tuple[str, str]:
    for pattern, precision in DATE_PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        parts = list(match.groups())
        if precision == "range_ymd":
            return f"{parts[0][2:]}{int(parts[1]):02d}{int(parts[2]):02d}-{parts[3][2:]}{int(parts[4]):02d}{int(parts[5]):02d}", "文件名候选"
        if precision == "range_ym":
            return f"{parts[0][2:]}{int(parts[1]):02d}-{parts[2][2:]}{int(parts[3]):02d}", "文件名候选"
        year = parts[0][2:] if len(parts[0]) == 4 else parts[0]
        token = year + "".join(f"{int(x):02d}" for x in parts[1:] if x is not None)
        return token, "文件名候选"
    return "时间待核", "未识别"


def clean_summary(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^待规范命名[_ -]*", "", stem)
    for pattern, _ in DATE_PATTERNS:
        stem = pattern.sub("", stem)
    stem = re.sub(r"(^|_)至(?=_|$)", r"\1", stem)
    stem = re.sub(r"[\\/:*?\"<>|]+", "-", stem)
    stem = re.sub(r"[_ .—-]{2,}", "_", stem).strip(" _-.—")
    return (stem or "材料名称待核")[:32]


def main() -> None:
    parser = argparse.ArgumentParser(description="生成待用户确认的分类改名方案")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--out", type=Path, default=Path("plan.json"))
    parser.add_argument("--directory-mode", choices=("default", "custom"), required=True)
    parser.add_argument("--custom-folder", action="append", default=[], help="自定义模式的一级目录，可重复提供")
    args = parser.parse_args()
    if args.directory_mode == "default" and args.custom_folder:
        raise SystemExit("默认目录模式不能同时提供 --custom-folder")
    if args.directory_mode == "custom" and not args.custom_folder:
        raise SystemExit("自定义目录模式至少需要一个 --custom-folder")
    directory_folders = list(DEFAULT_FOLDERS) if args.directory_mode == "default" else args.custom_folder
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    hash_counts = Counter(row["sha256"] for row in inventory["files"])
    hash_groups, next_group = {}, 1
    items = []
    for index, row in enumerate(inventory["files"], 1):
        token, date_source = date_token(row["original_name"])
        extension = row["extension"]
        new_name = f"{token}-{clean_summary(row['original_name'])}{extension}"
        duplicate_group = ""
        if hash_counts[row["sha256"]] > 1:
            duplicate_group = hash_groups.setdefault(row["sha256"], f"DUP-{next_group:03d}")
            if duplicate_group == f"DUP-{next_group:03d}":
                next_group += 1
        target_category = category(row["original_name"])
        if args.directory_mode == "custom" and target_category not in directory_folders:
            target_category = ""
        target_subcategory = basic_subcategory(row["original_name"]) if target_category == "002 基础资料" else ""
        items.append({
            **row,
            "material_id": f"MAT-{index:04d}",
            "target_category": target_category,
            "target_subcategory": target_subcategory,
            "proposed_name": new_name,
            "date_source": date_source,
            "duplicate_group": duplicate_group,
            "is_primary_analysis_file": duplicate_group == "" or not any(x.get("duplicate_group") == duplicate_group for x in items),
            "review_status": "待用户确认",
            "review_notes": "机器预览；需结合内容提取、主体消歧和版本关系复核",
        })
    basic_folders = sorted({item["target_subcategory"] for item in items if item["target_category"] == "002 基础资料"})
    payload = {
        "schema_version": "1.0",
        "source_folder": inventory["source_folder"],
        "confirmed": False,
        "directory_mode": args.directory_mode,
        "directory_structure": directory_folders,
        "directory_subfolders": {"002 基础资料": basic_folders} if basic_folders else {},
        "case_folder": {
            "sequence": "",
            "plaintiff_short_name": "",
            "defendant_short_name": "",
            "cause_of_action": "",
        },
        "case_folder_name": "",
        "case_summary": {},
        "entities": [],
        "events": [],
        "issues": [],
        "items": items,
    }
    directory_structure(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.out.resolve()), "items": len(items), "requires_confirmation": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()

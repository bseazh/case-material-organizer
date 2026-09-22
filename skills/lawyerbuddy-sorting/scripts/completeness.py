#!/usr/bin/env python3
"""Validate full-reading, fact disposition, and legal-fact review gates."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re


DISPOSITIONS = ("report_body", "timeline", "background", "pending_confirmation")
REVIEW_ROUNDS = ("full_extraction", "cross_material_review", "legal_fact_review")
ANALYSIS_MODES = ("mainline", "report", "exhaustive")


@dataclass(frozen=True)
class CompletenessResult:
    material_coverage_rate: float
    unit_coverage_rate: float
    fact_disposition_rate: float
    errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "material_coverage_rate": self.material_coverage_rate,
            "unit_coverage_rate": self.unit_coverage_rate,
            "fact_disposition_rate": self.fact_disposition_rate,
            "passed": self.passed,
            "errors": list(self.errors),
        }


def _ids(rows: object, key: str) -> list[str]:
    if not isinstance(rows, list):
        return []
    return [str(row.get(key) or "").strip() for row in rows if isinstance(row, dict)]


def _legal_relevant(fact: dict) -> bool:
    value = fact.get("legal_relevance")
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(str(value or "").strip())


def _references(value: object, prefix: str) -> set[str]:
    if isinstance(value, list):
        values = (str(item).strip() for item in value)
        return {item for item in values if item}
    return set(re.findall(rf"{re.escape(prefix)}-\d{{3,4}}", str(value or "")))


def _validate_report_content(
    plan: dict,
    material_ids: set[str],
    fact_ids: set[str],
    errors: list[str],
) -> None:
    entities = plan.get("entities") if isinstance(plan.get("entities"), list) else []
    if not entities:
        errors.append("案件主体为空，需要重新扫描主体名称、角色和来源材料")
    for index, entity in enumerate(entities, 1):
        if not isinstance(entity, dict):
            errors.append(f"案件主体第 {index} 项格式无效")
            continue
        if not str(entity.get("standard_name") or entity.get("name") or "").strip():
            errors.append(f"案件主体第 {index} 项缺少名称")
        if not str(entity.get("case_roles") or entity.get("role") or "").strip():
            errors.append(f"案件主体第 {index} 项缺少案件角色")
        sources = _references(entity.get("source_material_ids"), "MAT")
        if not sources:
            errors.append(f"案件主体第 {index} 项缺少来源材料")
        elif sources - material_ids:
            errors.append(f"案件主体第 {index} 项引用未知材料")

    summary = plan.get("case_summary") if isinstance(plan.get("case_summary"), dict) else {}
    for key in ("起因", "过程", "争议", "现状", "缺口"):
        if not str(summary.get(key) or "").strip():
            errors.append(f"案件总结“{key}”为空，需要重新扫描相关材料")

    all_events = plan.get("events") if isinstance(plan.get("events"), list) else []
    main_events = [
        event for event in all_events if isinstance(event, dict)
        and str(event.get("timeline_role") or event.get("timeline_section") or "main").lower()
        not in {"background", "背景", "背景信息"}
    ]
    if not main_events:
        errors.append("主线事件为空，需要根据事实台账重新合并事件")
    timeline_fact_ids: set[str] = set()
    for index, event in enumerate(main_events, 1):
        if not str(event.get("description") or "").strip():
            errors.append(f"主线事件第 {index} 项缺少中性事件描述")
        if not str(event.get("subjects") or "").strip():
            errors.append(f"主线事件第 {index} 项缺少涉及主体")
        material_refs = _references(event.get("all_material_ids") or event.get("material_ids"), "MAT")
        if not material_refs:
            errors.append(f"主线事件第 {index} 项缺少关联材料")
        elif material_refs - material_ids:
            errors.append(f"主线事件第 {index} 项引用未知材料")
        event_facts = _references(event.get("fact_ids"), "FACT")
        if not event_facts:
            errors.append(f"主线事件第 {index} 项缺少关联事实")
        elif event_facts - fact_ids:
            errors.append(f"主线事件第 {index} 项引用未知事实")
        timeline_fact_ids.update(event_facts)
    expected_timeline_facts = {
        str(value).strip()
        for value in (plan.get("fact_disposition") or {}).get("timeline", [])
        if str(value).strip()
    }
    if expected_timeline_facts - timeline_fact_ids:
        errors.append("部分时间轴事实尚未进入主线事件，需要重新合并事件")


def validate_completeness(plan: dict) -> CompletenessResult:
    errors: list[str] = []
    items = plan.get("items") if isinstance(plan.get("items"), list) else []
    material_ids = [str(item.get("material_id") or "").strip() for item in items if isinstance(item, dict)]
    valid_material_ids = {value for value in material_ids if value}
    if not material_ids:
        errors.append("没有材料，无法核验材料覆盖率")
    if len(valid_material_ids) != len(material_ids):
        errors.append("材料编号缺失或重复")

    coverage = plan.get("reading_coverage") if isinstance(plan.get("reading_coverage"), dict) else {}
    material_rows = coverage.get("materials") if isinstance(coverage.get("materials"), list) else []
    coverage_ids = _ids(material_rows, "material_id")
    coverage_counter = Counter(coverage_ids)
    missing_coverage = sorted(valid_material_ids - set(coverage_ids))
    extra_coverage = sorted(set(coverage_ids) - valid_material_ids)
    duplicate_coverage = sorted(key for key, count in coverage_counter.items() if key and count > 1)
    if missing_coverage:
        errors.append(f"缺少材料阅读记录：{'、'.join(missing_coverage)}")
    if extra_coverage:
        errors.append(f"阅读记录引用未知材料：{'、'.join(extra_coverage)}")
    if duplicate_coverage:
        errors.append(f"材料阅读记录重复：{'、'.join(duplicate_coverage)}")

    completed_materials = 0
    expected_units = 0
    completed_units = 0
    for row in material_rows:
        if not isinstance(row, dict) or str(row.get("material_id") or "").strip() not in valid_material_ids:
            continue
        material_id = str(row.get("material_id")).strip()
        status = str(row.get("status") or "").strip().lower()
        expected = row.get("units_expected")
        completed = row.get("units_completed")
        source_unit_labels = [str(value).strip() for value in row.get("source_units", []) if str(value).strip()]
        if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
            errors.append(f"{material_id} 的应读单元数缺失或无效")
            continue
        if len(set(source_unit_labels)) != expected:
            errors.append(f"{material_id} 的来源单元清单与应读数量不一致")
        if not isinstance(completed, int) or isinstance(completed, bool) or completed < 0:
            errors.append(f"{material_id} 的已读单元数缺失或无效")
            completed = 0
        if completed > expected:
            errors.append(f"{material_id} 的已读单元数超过应读数量")
        expected_units += expected
        completed_units += min(completed, expected)
        if not row.get("unit_type"):
            errors.append(f"{material_id} 未记录阅读单元类型")
        if not row.get("coverage_basis"):
            errors.append(f"{material_id} 未记录覆盖依据")
        completed_unit_labels = [str(value).strip() for value in row.get("completed_units", []) if str(value).strip()]
        if completed and not completed_unit_labels:
            errors.append(f"{material_id} 未列出已完成页码、工作表或分段")
        elif len(set(completed_unit_labels)) != completed:
            errors.append(f"{material_id} 的已完成单元明细与数量不一致")
        elif set(completed_unit_labels) - set(source_unit_labels):
            errors.append(f"{material_id} 的已完成单元包含来源清单之外的内容")
        elif status == "complete" and set(completed_unit_labels) != set(source_unit_labels):
            errors.append(f"{material_id} 的已完成单元未覆盖全部来源单元")
        if status != "complete" or completed < expected:
            errors.append(f"{material_id} 尚未完整读取（{completed}/{expected}）")
        else:
            completed_materials += 1

    material_rate = completed_materials / len(material_ids) if material_ids else 0.0
    unit_rate = completed_units / expected_units if expected_units else 0.0

    facts = plan.get("fact_inventory") if isinstance(plan.get("fact_inventory"), list) else []
    fact_ids = _ids(facts, "fact_id")
    valid_fact_ids = {value for value in fact_ids if value}
    if not facts:
        errors.append("事实台账为空，不能证明已经提取全部实质事实")
    if len(valid_fact_ids) != len(fact_ids):
        errors.append("事实编号缺失或重复")
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        fact_id = str(fact.get("fact_id") or "待编号")
        if not str(fact.get("statement") or "").strip():
            errors.append(f"{fact_id} 缺少中性事实表述")
        source_ids = {str(value).strip() for value in fact.get("source_material_ids", []) if str(value).strip()}
        if not source_ids:
            errors.append(f"{fact_id} 缺少来源材料")
        unknown_sources = source_ids - valid_material_ids
        if unknown_sources:
            errors.append(f"{fact_id} 引用未知材料：{'、'.join(sorted(unknown_sources))}")
        if not fact.get("source_locations"):
            errors.append(f"{fact_id} 缺少原文定位")
        if not fact.get("record_nature"):
            errors.append(f"{fact_id} 缺少记载性质")

    materials_with_facts = {
        str(material_id).strip()
        for fact in facts
        if isinstance(fact, dict)
        for material_id in fact.get("source_material_ids", [])
        if str(material_id).strip()
    }
    for row in material_rows:
        if not isinstance(row, dict):
            continue
        material_id = str(row.get("material_id") or "").strip()
        if material_id in valid_material_ids and material_id not in materials_with_facts:
            if not str(row.get("no_relevant_fact_reason") or "").strip():
                errors.append(f"{material_id} 未提取事实，也未说明未发现相关实质事实的原因")

    disposition = plan.get("fact_disposition") if isinstance(plan.get("fact_disposition"), dict) else {}
    disposed_ids: list[str] = []
    for bucket in DISPOSITIONS:
        values = disposition.get(bucket)
        if not isinstance(values, list):
            errors.append(f"事实去向缺少列表：{bucket}")
            continue
        disposed_ids.extend(str(value).strip() for value in values if str(value).strip())
    disposition_counter = Counter(disposed_ids)
    duplicate_disposition = sorted(key for key, count in disposition_counter.items() if count > 1)
    unknown_disposition = sorted(set(disposed_ids) - valid_fact_ids)
    missing_disposition = sorted(valid_fact_ids - set(disposed_ids))
    if duplicate_disposition:
        errors.append(f"事实存在多个主要去向：{'、'.join(duplicate_disposition)}")
    if unknown_disposition:
        errors.append(f"事实去向引用未知事实：{'、'.join(unknown_disposition)}")
    if missing_disposition:
        errors.append(f"事实尚未确定最终去向：{'、'.join(missing_disposition)}")
    disposed_valid = len(valid_fact_ids & set(disposed_ids))
    fact_rate = disposed_valid / len(valid_fact_ids) if valid_fact_ids else 0.0

    legal_map = plan.get("legal_fact_map") if isinstance(plan.get("legal_fact_map"), list) else []
    mapped_legal_fact_ids: set[str] = set()
    for index, entry in enumerate(legal_map, 1):
        if not isinstance(entry, dict):
            errors.append(f"法律事实映射第 {index} 项格式无效")
            continue
        if not str(entry.get("legal_element") or "").strip():
            errors.append(f"法律事实映射第 {index} 项缺少法律要素")
        if not str(entry.get("evidence_status") or "").strip():
            errors.append(f"法律事实映射第 {index} 项缺少证据状态")
        entry_ids = {str(value).strip() for value in entry.get("fact_ids", []) if str(value).strip()}
        if not entry_ids:
            errors.append(f"法律事实映射第 {index} 项缺少关联事实")
        unknown = entry_ids - valid_fact_ids
        if unknown:
            errors.append(f"法律事实映射引用未知事实：{'、'.join(sorted(unknown))}")
        mapped_legal_fact_ids.update(entry_ids & valid_fact_ids)
    relevant_ids = {
        str(fact.get("fact_id")).strip()
        for fact in facts
        if isinstance(fact, dict) and _legal_relevant(fact) and str(fact.get("fact_id") or "").strip()
    }
    if facts and not relevant_ids:
        errors.append("尚未识别任何具有法律相关性的事实")
    missing_legal_map = sorted(relevant_ids - mapped_legal_fact_ids)
    if missing_legal_map:
        errors.append(f"具有法律相关性的事实尚未映射法律要素：{'、'.join(missing_legal_map)}")

    rounds = coverage.get("review_rounds") if isinstance(coverage.get("review_rounds"), dict) else {}
    for name in REVIEW_ROUNDS:
        review = rounds.get(name) if isinstance(rounds.get(name), dict) else {}
        if review.get("completed") is not True:
            errors.append(f"三轮复核尚未完成：{name}")
            continue
        reviewed_materials = {str(value).strip() for value in review.get("reviewed_material_ids", []) if str(value).strip()}
        reviewed_facts = {str(value).strip() for value in review.get("reviewed_fact_ids", []) if str(value).strip()}
        if name == "full_extraction":
            if reviewed_materials != valid_material_ids:
                errors.append("完整提取复核未覆盖全部材料")
            if reviewed_facts != valid_fact_ids:
                errors.append("完整提取复核未覆盖全部事实")
        if name == "cross_material_review":
            if reviewed_materials != valid_material_ids:
                errors.append("跨材料复核未覆盖全部材料")
            if reviewed_facts != valid_fact_ids:
                errors.append("跨材料复核未覆盖全部事实")
        if name == "legal_fact_review":
            if reviewed_materials != valid_material_ids:
                errors.append("法律事实复核未覆盖全部材料")
            if reviewed_facts != relevant_ids:
                errors.append("法律事实复核未覆盖全部法律相关事实")

    if material_rate != 1.0:
        errors.append(f"材料覆盖率未达到 100%（{material_rate:.2%}）")
    if unit_rate != 1.0:
        errors.append(f"阅读单元覆盖率未达到 100%（{unit_rate:.2%}）")
    if fact_rate != 1.0:
        errors.append(f"事实处置率未达到 100%（{fact_rate:.2%}）")

    return CompletenessResult(material_rate, unit_rate, fact_rate, tuple(dict.fromkeys(errors)))


def require_completeness(plan: dict) -> CompletenessResult:
    result = validate_completeness(plan)
    if not result.passed:
        details = "\n- ".join(result.errors)
        raise ValueError(f"完整性检查未通过，不能生成正式案件报告：\n- {details}")
    return result


def validate_analysis_readiness(plan: dict, *, require_report: bool = False) -> CompletenessResult:
    """Validate the selected key-material scope without requiring every page of every file."""
    # Legacy plans without an explicit mode remain strict instead of silently downgrading.
    mode = str(plan.get("processing_mode") or "exhaustive").strip().lower()
    errors: list[str] = []
    if mode == "exhaustive":
        errors.extend(validate_completeness(plan).errors)
    if mode not in ANALYSIS_MODES:
        errors.append("当前仅完成快速归档，尚未选择案件内容分析")
    if require_report and mode not in {"report", "exhaustive"}:
        errors.append("尚未选择正式案件报告模式")

    items = plan.get("items") if isinstance(plan.get("items"), list) else []
    material_ids = {
        str(item.get("material_id") or "").strip()
        for item in items if isinstance(item, dict) and str(item.get("material_id") or "").strip()
    }
    scope = plan.get("analysis_scope") if isinstance(plan.get("analysis_scope"), dict) else {}

    def scope_ids(name: str) -> set[str]:
        values = scope.get(name)
        return {str(value).strip() for value in values if str(value).strip()} if isinstance(values, list) else set()

    key_ids = scope_ids("key_material_ids")
    reviewed_ids = scope_ids("reviewed_material_ids")
    machine_ids = scope_ids("machine_extracted_material_ids")
    deferred_ids = scope_ids("deferred_material_ids")
    unreadable_ids = scope_ids("unreadable_material_ids")
    if mode == "exhaustive" and not scope:
        coverage = plan.get("reading_coverage") if isinstance(plan.get("reading_coverage"), dict) else {}
        coverage_rows = coverage.get("materials") if isinstance(coverage.get("materials"), list) else []
        key_ids = set(material_ids)
        reviewed_ids = {
            str(row.get("material_id") or "").strip()
            for row in coverage_rows if isinstance(row, dict) and row.get("status") == "complete"
        }
    referenced = key_ids | reviewed_ids | machine_ids | deferred_ids | unreadable_ids
    unknown = referenced - material_ids
    if unknown:
        errors.append(f"分析范围引用未知材料：{'、'.join(sorted(unknown))}")
    unaccounted = material_ids - (reviewed_ids | machine_ids | deferred_ids | unreadable_ids)
    if unaccounted:
        errors.append(f"以下材料尚未进入任何阅读或处置范围：{'、'.join(sorted(unaccounted))}")
    if not material_ids:
        errors.append("没有已登记材料")
    if not key_ids:
        errors.append("尚未确定本案关键材料")
    missing_key_review = key_ids - reviewed_ids
    if missing_key_review:
        errors.append(f"关键材料尚未完成阅读：{'、'.join(sorted(missing_key_review))}")
    if mode != "exhaustive" and not str(scope.get("selection_basis") or "").strip():
        errors.append("尚未说明关键材料的选择依据")

    facts = plan.get("fact_inventory") if isinstance(plan.get("fact_inventory"), list) else []
    fact_ids = _ids(facts, "fact_id")
    valid_fact_ids = {value for value in fact_ids if value}
    if not facts:
        errors.append("尚未提取可追溯的案件事实")
    if len(valid_fact_ids) != len(fact_ids):
        errors.append("事实编号缺失或重复")
    fact_sources: set[str] = set()
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        fact_id = str(fact.get("fact_id") or "待编号")
        if not str(fact.get("statement") or "").strip():
            errors.append(f"{fact_id} 缺少中性事实表述")
        source_ids = {str(value).strip() for value in fact.get("source_material_ids", []) if str(value).strip()}
        fact_sources.update(source_ids)
        if not source_ids:
            errors.append(f"{fact_id} 缺少来源材料")
        if source_ids - material_ids:
            errors.append(f"{fact_id} 引用未知材料")
        if source_ids - reviewed_ids:
            errors.append(f"{fact_id} 引用了尚未核对的材料")
        if not fact.get("source_locations"):
            errors.append(f"{fact_id} 缺少原文定位")
        if not fact.get("record_nature"):
            errors.append(f"{fact_id} 缺少记载性质")

    disposition = plan.get("fact_disposition") if isinstance(plan.get("fact_disposition"), dict) else {}
    disposed_ids = [
        str(value).strip()
        for bucket in DISPOSITIONS
        for value in (disposition.get(bucket) if isinstance(disposition.get(bucket), list) else [])
        if str(value).strip()
    ]
    disposition_counter = Counter(disposed_ids)
    if any(count > 1 for count in disposition_counter.values()):
        errors.append("事实存在多个主要去向")
    if valid_fact_ids - set(disposed_ids):
        errors.append("部分事实尚未确定最终去向")

    legal_map = plan.get("legal_fact_map") if isinstance(plan.get("legal_fact_map"), list) else []
    mapped_ids: set[str] = set()
    for entry in legal_map:
        if not isinstance(entry, dict):
            continue
        if not str(entry.get("legal_element") or "").strip():
            errors.append("法律事实映射缺少法律要素")
        if not str(entry.get("evidence_status") or "").strip():
            errors.append("法律事实映射缺少证据状态")
        mapped_ids.update(str(value).strip() for value in entry.get("fact_ids", []) if str(value).strip())
    relevant_ids = {
        str(fact.get("fact_id") or "").strip()
        for fact in facts if isinstance(fact, dict) and _legal_relevant(fact)
    }
    if relevant_ids - mapped_ids:
        errors.append("部分法律相关事实尚未映射法律要素")

    if require_report or mode == "exhaustive":
        _validate_report_content(plan, material_ids, valid_fact_ids, errors)

    material_rate = len(reviewed_ids & material_ids) / len(material_ids) if material_ids else 0.0
    fact_rate = len(valid_fact_ids & set(disposed_ids)) / len(valid_fact_ids) if valid_fact_ids else 0.0
    return CompletenessResult(material_rate, 0.0, fact_rate, tuple(dict.fromkeys(errors)))


def require_analysis_readiness(plan: dict, *, require_report: bool = False) -> CompletenessResult:
    result = validate_analysis_readiness(plan, require_report=require_report)
    if not result.passed:
        details = "\n- ".join(result.errors)
        raise ValueError(f"案件分析范围检查未通过：\n- {details}")
    return result

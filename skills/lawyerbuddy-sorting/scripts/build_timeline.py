#!/usr/bin/env python3
"""Render one confirmed case timeline as deterministic, print-ready HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from case_naming import timeline_filename, timeline_title
from completeness import require_analysis_readiness


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def split_cn(value: object) -> list[str]:
    return [part.strip() for part in re.split(r"[；;\n]+", str(value or "")) if part.strip()]


def year_of(value: object) -> str:
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return match.group(0) if match else "日期待确认"


def event_fingerprint(events: list[dict]) -> str:
    payload = json.dumps(events, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def display_date(value: object) -> str:
    raw = str(value or "日期待确认").strip()
    match = re.fullmatch(r"(20\d{2})-(\d{2})-(\d{2})(?:至|到|—|~)(20\d{2})-(\d{2})-(\d{2})", raw)
    if match:
        first_year, first_month, first_day, last_year, last_month, last_day = match.groups()
        if first_year == last_year:
            return f"{first_year}.{first_month}.{first_day}—{last_month}.{last_day}"
        return f"{first_year}.{first_month}.{first_day}—{last_year}.{last_month}.{last_day}"
    match = re.fullmatch(r"(20\d{2})-(\d{2})-(\d{2})", raw)
    if match:
        return ".".join(match.groups())
    return raw.replace("至", "—")


def link_for(path: Path, output_dir: Path) -> str:
    relative = Path(os.path.relpath(path, output_dir))
    return "/".join(quote(part) for part in relative.parts)


def file_kind(name: str) -> str:
    suffix = Path(name).suffix.lstrip(".").upper()
    return suffix[:5] if suffix else "FILE"


def plan_material_names(event: dict, by_id: dict[str, dict]) -> str:
    material_ids = re.findall(r"MAT-\d{4}", str(event.get("all_material_ids") or event.get("material_ids") or ""))
    names = []
    for material_id in material_ids:
        item = by_id.get(material_id, {})
        name = item.get("proposed_name") or item.get("original_name")
        if name and name not in names:
            names.append(str(name))
    if not names:
        names = [Path(value).name for value in split_cn(event.get("archive_paths") or event.get("related_materials"))]
    return "；".join(name for name in names if name)


def event_state(event: dict) -> tuple[str, str]:
    check = str(event.get("待确认事项") or "")
    combined = f"{event.get('事件', '')} {check}"
    if any(word in combined for word in ("冲突", "不一致", "异议", "争议", "不同")):
        return "disputed", "存在争议"
    if check not in {"", "无", "无。"}:
        return "pending", "仍需补充"
    return "verified", "材料记载"


def load_source(source: Path) -> tuple[dict, list[dict], dict[str, str], list[dict], Path]:
    if source.suffix.lower() != ".json":
        raise SystemExit("时间轴输入必须是已执行的归档方案 JSON")
    plan = json.loads(source.read_text(encoding="utf-8"))
    if not plan.get("confirmed"):
        raise SystemExit("只能根据已确认并执行的归档方案生成时间轴")
    media_check = plan.get("media_check", {})
    if media_check and not media_check.get("ready_for_case_analysis", False):
        raise SystemExit("录音逐字稿检查尚未通过，不能生成时间轴")
    if media_check.get("recording_count", 0) and not plan.get("transcript_mainline_review"):
        raise SystemExit("尚未记录逐字稿候选主线与全量材料反向核查，不能生成时间轴")
    try:
        require_analysis_readiness(plan)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    items = plan.get("items", [])
    by_id = {str(item.get("material_id")): item for item in items}
    events = []
    for event in plan.get("events", []):
        role = str(event.get("timeline_role") or event.get("timeline_section") or "main").lower()
        if role in {"background", "背景", "背景信息"}:
            continue
        events.append({
            "日期": event.get("event_time") or "日期待确认",
            "事件": event.get("description") or "事件内容待确认",
            "相关人员/公司": event.get("subjects") or "相关主体待确认",
            "相关材料": plan_material_names(event, by_id),
            "待确认事项": event.get("conflicts") or event.get("issues") or "无",
            "阶段": event.get("timeline_phase") or event.get("phase") or year_of(event.get("event_time")),
            "记载性质": event.get("record_type") or "材料记载",
        })
    events.sort(key=lambda event: (year_of(event["日期"]) == "日期待确认", str(event["日期"]), str(event["事件"])))
    raw_main_events = sorted(
        (
            event for event in plan.get("events", []) if isinstance(event, dict)
            and str(event.get("timeline_role") or event.get("timeline_section") or "main").lower()
            not in {"background", "背景", "背景信息"}
        ),
        key=lambda event: (re.search(r"(?:19|20)\d{2}", str(event.get("event_time") or "")) is None, str(event.get("event_time") or "")),
    )
    handoff = plan.get("workflow_handoff") if isinstance(plan.get("workflow_handoff"), dict) else {}
    report_path = Path(str(handoff.get("report_path") or ""))
    if not report_path.is_file():
        raise SystemExit("尚未生成可读取的 Word 案件梳理报告，不能生成可视化时间轴")
    expected_snapshot = str(handoff.get("report_event_snapshot_sha256") or "")
    if not expected_snapshot or expected_snapshot != event_fingerprint(raw_main_events):
        raise SystemExit("案件事件在报告生成后发生变化，请先重新生成 Word 报告，再生成时间轴")
    overview = {key: str(plan.get("case_summary", {}).get(key) or "") for key in ("起因", "过程", "争议", "现状", "缺口")}
    archive_root = Path(plan.get("result_folder") or source.parent.parent.parent)
    return plan, events, overview, plan.get("issues", []), archive_root


def issue_cards(issues: list[dict], overview: dict[str, str]) -> str:
    cards = []
    for index, issue in enumerate(issues[:4], 1):
        title = issue.get("issue") or issue.get("description") or issue.get("impact") or "争议事项待确认"
        detail = issue.get("recommended_action") or issue.get("basis") or issue.get("impact") or "需结合现有材料进一步核对。"
        cards.append(f'<article class="issue"><strong>{index:02d} {esc(title)}</strong><p>{esc(detail)}</p></article>')
    if not cards and overview.get("争议"):
        cards.append(f'<article class="issue"><strong>01 主要争议</strong><p>{esc(overview["争议"])}</p></article>')
    return "".join(cards) or '<article class="issue neutral"><strong>争议事项待梳理</strong><p>当前方案尚未形成可展示的争议摘要。</p></article>'


def main() -> None:
    parser = argparse.ArgumentParser(description="从已执行归档方案 JSON 生成时间轴 HTML")
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--notice", default="仅依据当前已归档材料整理")
    args = parser.parse_args()

    plan, events, overview, issues, archive_root = load_source(args.source)
    expected_filename = timeline_filename(plan)
    output = args.out or (archive_root / "整理结果" / expected_filename)
    if output.suffix.lower() != ".html":
        output = output / expected_filename
    if output.name != expected_filename:
        raise SystemExit(f"时间轴文件名必须与确认案由一致，应为：{expected_filename}")

    archive_index: dict[str, list[Path]] = {}
    material_folders = sorted(path for path in archive_root.iterdir() if path.is_dir() and path.name != "整理结果" and not path.name.startswith("."))
    for base in material_folders:
        for path in base.rglob("*"):
            if path.is_file():
                archive_index.setdefault(path.name, []).append(path)

    cards = []
    current_phase = None
    for event in events:
        phase = str(event.get("阶段") or "日期待确认")
        if phase != current_phase:
            current_phase = phase
            cards.append(f'<div class="phase"><span>{esc(phase)}</span></div>')
        state, state_label = event_state(event)
        evidence = []
        for name in split_cn(event.get("相关材料")):
            candidates = archive_index.get(name, [])
            label = f'<a href="{link_for(candidates[0], output.parent.resolve())}">{esc(name)}</a>' if len(candidates) == 1 else esc(name)
            evidence.append(f'<span><b>{esc(file_kind(name))}</b>{label}</span>')
        evidence_html = f'<div class="evidence">{"".join(evidence)}</div>' if evidence else ""
        check = str(event.get("待确认事项") or "无")
        check_html = "" if check in {"", "无", "无。"} else f'<p class="check"><b>待确认：</b>{esc(check)}</p>'
        cards.append(f'''<article class="event {state}">
  <div class="date"><strong>{esc(display_date(event["日期"]))}</strong><span>{esc(event["记载性质"])}</span></div><div class="node"></div>
  <div class="card"><div class="card-top"><span class="tag">{esc(state_label)}</span></div>
    <h3>{esc(event["事件"])}</h3><p class="fact"><b>相关主体：</b>{esc(event["相关人员/公司"])}</p>
    {evidence_html}{check_html}
  </div>
</article>''')

    dated = [event for event in events if year_of(event["日期"]) != "日期待确认"]
    first_date = dated[0]["日期"] if dated else "待确认"
    last_date = dated[-1]["日期"] if dated else "待确认"
    material_count = len({name for event in events for name in split_cn(event.get("相关材料"))})
    case = plan.get("case_folder") or {}
    parties = f"{case.get('plaintiff_short_name', '原告待确认')} VS {case.get('defendant_short_name', '被告待确认')}"
    review = plan.get("cause_of_action_review") or {}
    secondary_text = "、".join(str(value) for value in review.get("secondary_causes") or []) or "无"
    reading_tips = [overview.get("现状") or "案件当前状态待根据材料补充。", overview.get("缺口") or "待补材料与待核事项见各时间轴节点。", "时间轴中的“待确认”表示材料不足或记载不一致，不代表事实结论。"]
    tip_html = "".join(f"<li>{esc(value)}</li>" for value in reading_tips)
    title = timeline_title(plan)

    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>
:root{{--navy:#183f73;--navy2:#285486;--blue:#356fc3;--red:#c83a46;--redsoft:#fff3f3;--gold:#b78625;--goldsoft:#fff8e8;--ink:#202b38;--muted:#687585;--ground:#f3f6fa;--paper:#fff}}
*{{box-sizing:border-box}}html{{background:var(--ground)}}body{{margin:0;color:var(--ink);background:var(--ground);font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif;letter-spacing:0}}main{{width:min(920px,calc(100% - 32px));margin:0 auto;padding:28px 0 52px}}
.hero{{padding:36px 40px 30px;color:#fff;background:var(--navy);border-radius:7px;box-shadow:0 8px 20px rgba(25,53,91,.14)}}.eyebrow{{margin:0 0 14px;color:#bcd0e9;font-size:11px;font-weight:700}}h1{{margin:0;font-size:30px;line-height:1.25}}.subtitle{{margin:10px 0 0;color:#dce6f2;font-size:13px;line-height:1.7}}
.hero-grid{{display:grid;grid-template-columns:1.2fr 1.2fr .8fr;gap:24px;margin-top:28px;padding-top:20px;border-top:1px solid rgba(255,255,255,.2)}}.hero-grid span{{display:block;margin-bottom:7px;color:#aac0db;font-size:10px}}.hero-grid strong{{display:block;font-size:13px;line-height:1.55}}.metrics{{display:flex;gap:24px;margin-top:18px;color:#cbd9e9;font-size:10px}}.metrics b{{margin-right:4px;color:#fff;font-size:14px}}
.legend{{display:flex;flex-wrap:wrap;gap:18px;margin:16px 0 30px;padding:15px 18px;background:#fff;border:1px solid #e1e7ef;border-radius:6px;font-size:11px;color:#556273}}.legend>strong{{color:var(--ink)}}.legend i{{display:inline-block;width:8px;height:8px;margin-right:7px;border-radius:2px}}.legend .blue{{background:var(--blue)}}.legend .red{{background:var(--red)}}.legend .gold{{background:var(--gold)}}
.section-head{{display:flex;align-items:baseline;gap:14px;margin:0 0 14px}}.section-head h2{{margin:0;font-size:19px}}.section-head p{{margin:0;color:var(--muted);font-size:11px}}.issues{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:32px}}.issue{{padding:16px 17px 15px;background:var(--redsoft);border:1px solid #efcfd1;border-radius:6px}}.issue.neutral{{background:#fff;border-color:#dce3ec}}.issue strong{{display:block;margin-bottom:7px;color:#b62e3a;font-size:13px}}.issue p{{margin:0;color:#4a5664;font-size:11px;line-height:1.7}}
.timeline{{position:relative;padding-top:2px}}.timeline:before{{content:"";position:absolute;top:30px;bottom:34px;left:124px;width:2px;background:#c9d4e2}}.phase{{position:relative;display:flex;align-items:center;gap:12px;margin:26px 0 14px 105px}}.phase:after{{content:"";height:1px;flex:1;background:#cfd8e4}}.phase span{{position:relative;z-index:1;padding:7px 13px;color:#fff;background:var(--navy);border-radius:16px;font-size:11px;font-weight:700}}
.event{{--accent:var(--blue);position:relative;display:grid;grid-template-columns:98px 28px 1fr;gap:0 14px;margin-bottom:14px}}.event.disputed{{--accent:var(--red)}}.event.pending{{--accent:var(--gold)}}.date{{padding-top:18px;text-align:right}}.date strong{{display:block;color:var(--accent);font-size:14px;line-height:1.35}}.date span{{display:block;margin-top:4px;color:#8a96a5;font-size:9px}}.node{{position:relative}}.node:before{{content:"";position:absolute;z-index:2;top:20px;left:7px;width:12px;height:12px;background:#fff;border:4px solid var(--accent);border-radius:50%;box-shadow:0 0 0 4px var(--ground)}}
.card{{padding:17px 19px 16px;background:var(--paper);border:1px solid #dce3ec;border-left:4px solid var(--accent);border-radius:6px;box-shadow:0 3px 10px rgba(26,49,79,.055)}}.card-top{{display:flex;gap:7px;margin-bottom:9px}}.tag{{padding:4px 7px;color:var(--navy2);background:#eaf1fa;border-radius:3px;font-size:9px;font-weight:700}}.disputed .tag{{color:#ad2d37;background:#fde8e9}}.pending .tag{{color:#8b6419;background:var(--goldsoft)}}.card h3{{margin:0 0 8px;font-size:15px;line-height:1.55}}.fact{{margin:0;color:#475463;font-size:11px;line-height:1.75}}.fact b{{color:#687585;font-size:10px}}
.evidence{{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}}.evidence span{{display:flex;max-width:100%;overflow-wrap:anywhere;color:#536477;background:#f4f6f9;border:1px solid #dfe5ec;border-radius:3px;font-size:9px}}.evidence b{{display:flex;align-items:center;margin-right:6px;padding:5px;background:#e4eaf1;color:#5a6878;font-size:8px}}.evidence a,.evidence span{{padding-right:7px}}.evidence a{{padding-top:5px;padding-bottom:5px;color:#315f8f;text-decoration:none}}
.check{{margin:12px 0 0;padding:10px 11px;color:#8e3038;background:#fff4f4;border-left:3px solid var(--red);font-size:10px;line-height:1.65}}.reading{{margin-top:28px;padding:20px 22px;background:#fff;border:1px solid #dce3ec;border-radius:6px}}.reading h2{{margin:0 0 10px;font-size:15px}}.reading ul{{margin:0;padding-left:18px}}.reading li{{margin:6px 0;color:#4d5968;font-size:11px;line-height:1.7}}footer{{margin-top:24px;color:#7c8794;font-size:9px;line-height:1.7;text-align:center}}
@media(max-width:640px){{main{{width:calc(100% - 18px);padding-top:10px}}.hero{{padding:25px 20px}}h1{{font-size:23px}}.hero-grid{{grid-template-columns:1fr;gap:12px}}.metrics{{flex-wrap:wrap}}.issues{{grid-template-columns:1fr}}.timeline:before{{left:86px}}.phase{{margin-left:67px}}.event{{grid-template-columns:64px 22px 1fr;gap:0 9px}}.date strong{{font-size:10px}}.node:before{{left:3px;width:10px;height:10px;border-width:3px}}.card{{padding:15px 14px}}.card h3{{font-size:14px}}}}
@media print{{@page{{size:A4;margin:12mm}}html,body{{background:#fff}}main{{width:100%;padding:0}}.hero,.tag,.phase span,.node:before{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}.event,.issue{{break-inside:avoid}}}}
</style></head><body><main>
<header class="hero"><p class="eyebrow">CASE TIMELINE · 案件关键时间轴</p><h1>{esc(title)}</h1><p class="subtitle">{esc(parties)} · {esc(args.notice)}；不构成事实认定或法律结论。</p>
<div class="hero-grid"><div><span>主要案由</span><strong>{esc(review.get("primary_cause"))}</strong></div><div><span>其他关联案由</span><strong>{esc(secondary_text)}</strong></div><div><span>时间跨度</span><strong>{esc(first_date)}—{esc(last_date)}</strong></div></div><div class="metrics"><span><b>{len(events)}</b>主线事件</span><span><b>{material_count}</b>关联材料</span><span><b>{len(issues)}</b>待核事项</span></div></header>
<div class="legend"><strong>图例</strong><span><i class="blue"></i>材料能够相互印证</span><span><i class="red"></i>存在争议或材料冲突</span><span><i class="gold"></i>仍需补充材料</span></div>
<section><div class="section-head"><h2>关键争议速览</h2><p>先看争点，再进入完整时间线</p></div><div class="issues">{issue_cards(issues, overview)}</div></section>
<section><div class="section-head"><h2>完整时间轴</h2><p>按案件阶段呈现与争议直接相关的关键事件</p></div><div class="timeline">{"".join(cards)}</div></section>
<section class="reading"><h2>当前材料阅读提示</h2><ul>{tip_html}</ul></section>
<footer>本时间轴仅依据已归档材料整理。逐字稿应与录音原声核对；文字识别不清及主体、日期、金额不一致之处均应回查原件。</footer>
</main></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    handoff = plan.setdefault("workflow_handoff", {})
    handoff.update({
        "completed_skill": "lawyerbuddy-timeline",
        "recommended_next_skill": "",
        "case_root": str(archive_root.resolve()),
        "plan_path": str(args.source.resolve()),
        "timeline_path": str(output.resolve()),
    })
    args.source.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output.resolve())


if __name__ == "__main__":
    main()

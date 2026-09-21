#!/usr/bin/env python3
"""Check recording-to-transcript coverage before substantive case analysis."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MEDIA = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".mp4", ".mov", ".avi", ".mkv"}
TRANSCRIPT_FORMATS = {".txt", ".md", ".docx", ".pdf"}
TRANSCRIPT_MARKERS = ("逐字稿", "转写原文", "录音转写", "会议转写", "语音转写")
RECORDING_DOCUMENT_MARKERS = ("录音", "语音", "会谈", "访谈")
TRANSCRIPTION_SERVICE = "https://tingwu.aliyun.com/home"


def compact_stem(name: str) -> str:
    stem = Path(name).stem.lower()
    for marker in TRANSCRIPT_MARKERS:
        stem = stem.replace(marker.lower(), "")
    stem = re.sub(r"[\s_（）()【】\[\]—-]+", "", stem)
    return stem


def date_tokens(name: str) -> set[str]:
    tokens = set(re.findall(r"(?<!\d)(?:20)?\d{2}[01]\d[0-3]\d(?!\d)", name))
    tokens.update(re.findall(r"(?<!\d)20\d{2}[-_.年][01]?\d[-_.月][0-3]?\d", name))
    return {re.sub(r"\D", "", token)[-6:] for token in tokens}


def main() -> None:
    parser = argparse.ArgumentParser(description="在案件分析前检查录音是否有对应逐字稿")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--out", type=Path, default=Path("media-check.json"))
    parser.add_argument(
        "--confirm",
        action="append",
        default=[],
        metavar="录音相对路径=逐字稿相对路径",
        help="记录用户已确认的录音与逐字稿对应关系，可重复提供",
    )
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    files = inventory.get("files", [])
    media = [item for item in files if str(item.get("extension", "")).lower() in MEDIA]
    text_files = [
        item for item in files
        if str(item.get("extension", "")).lower() in TRANSCRIPT_FORMATS
    ]
    transcript_candidates = [
        item for item in text_files
        if any(marker in str(item.get("original_name", "")) for marker in TRANSCRIPT_MARKERS)
    ]
    recording_document_candidates = [
        item for item in text_files
        if any(marker in str(item.get("original_name", "")) for marker in RECORDING_DOCUMENT_MARKERS)
    ]
    known_paths = {
        str(item.get("original_relative_path", "")): item
        for item in files
    }
    confirmed_pairs: dict[str, str] = {}
    for raw in args.confirm:
        if "=" not in raw:
            raise SystemExit("--confirm 格式应为：录音相对路径=逐字稿相对路径")
        recording_path, transcript_path = (part.strip() for part in raw.split("=", 1))
        recording_item = known_paths.get(recording_path)
        transcript_item = known_paths.get(transcript_path)
        if not recording_item or str(recording_item.get("extension", "")).lower() not in MEDIA:
            raise SystemExit(f"确认关系中的录音不存在或格式不支持：{recording_path}")
        if not transcript_item or str(transcript_item.get("extension", "")).lower() not in TRANSCRIPT_FORMATS:
            raise SystemExit(f"确认关系中的逐字稿不存在或格式不支持：{transcript_path}")
        if recording_path in confirmed_pairs and confirmed_pairs[recording_path] != transcript_path:
            raise SystemExit(f"同一录音不能确认多个主要逐字稿：{recording_path}")
        confirmed_pairs[recording_path] = transcript_path

    checks = []
    for recording in media:
        recording_name = str(recording.get("original_name", ""))
        recording_path = str(recording.get("original_relative_path", ""))
        key = compact_stem(recording_name)
        strong = [item for item in text_files if compact_stem(str(item.get("original_name", ""))) == key]
        if recording_path in confirmed_pairs:
            status = "matched"
            matched = confirmed_pairs[recording_path]
            candidates = [matched]
        elif len(strong) == 1:
            status = "matched"
            matched = str(strong[0].get("original_relative_path", ""))
            candidates = [matched]
        elif len(strong) > 1:
            status = "ambiguous"
            matched = ""
            candidates = [str(item.get("original_relative_path", "")) for item in strong]
        else:
            dates = date_tokens(recording_name)
            same_date = [
                item for item in transcript_candidates + recording_document_candidates
                if dates and dates.intersection(date_tokens(str(item.get("original_name", ""))))
            ]
            same_date = list({str(item.get("original_relative_path", "")): item for item in same_date}.values())
            status = "ambiguous" if same_date else "missing"
            matched = ""
            candidates = [str(item.get("original_relative_path", "")) for item in same_date]
        checks.append({
            "recording": str(recording.get("original_relative_path", "")),
            "status": status,
            "matched_transcript": matched,
            "candidate_transcripts": candidates,
            "confirmed_by_user": recording_path in confirmed_pairs,
        })

    missing = [row["recording"] for row in checks if row["status"] == "missing"]
    ambiguous = [row["recording"] for row in checks if row["status"] == "ambiguous"]
    payload = {
        "schema_version": "1.0",
        "source_folder": inventory.get("source_folder", ""),
        "recording_count": len(media),
        "matched_count": sum(row["status"] == "matched" for row in checks),
        "missing_transcripts": missing,
        "ambiguous_matches": ambiguous,
        "recordings": checks,
        "ready_for_case_analysis": not missing and not ambiguous,
        "requires_user_action": bool(missing or ambiguous),
        "transcription_service": TRANSCRIPTION_SERVICE if missing else "",
        "user_message_required": bool(missing or ambiguous),
        "next_action": (
            f"请打开阿里云听悟完成转写：{TRANSCRIPTION_SERVICE}"
            if missing else
            "请确认录音与候选逐字稿的对应关系"
            if ambiguous else
            "录音逐字稿检查已通过"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(args.out.resolve()),
        "recordings": len(media),
        "matched": payload["matched_count"],
        "missing": len(missing),
        "ambiguous": len(ambiguous),
        "ready_for_case_analysis": payload["ready_for_case_analysis"],
        "next_action": payload["next_action"],
        "transcription_service": payload["transcription_service"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

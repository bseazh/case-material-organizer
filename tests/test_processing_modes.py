from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "lawyerbuddy-sorting" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from completeness import validate_analysis_readiness  # noqa: E402


def targeted_plan(mode: str = "report") -> dict:
    return {
        "processing_mode": mode,
        "items": [
            {"material_id": "MAT-0001", "original_name": "合同.pdf"},
            {"material_id": "MAT-0002", "original_name": "背景附件.pdf"},
        ],
        "analysis_scope": {
            "key_material_ids": ["MAT-0001"],
            "reviewed_material_ids": ["MAT-0001"],
            "machine_extracted_material_ids": ["MAT-0002"],
            "deferred_material_ids": ["MAT-0002"],
            "unreadable_material_ids": [],
            "selection_basis": "合同直接记载争议法律关系和履行期限。",
        },
        "fact_inventory": [{
            "fact_id": "FACT-001",
            "statement": "合同记载付款期限为签署后十日内。",
            "record_nature": "书面约定",
            "source_material_ids": ["MAT-0001"],
            "source_locations": ["第3页付款条款"],
            "legal_relevance": ["付款期限"],
        }],
        "fact_disposition": {
            "report_body": ["FACT-001"],
            "timeline": [],
            "background": [],
            "pending_confirmation": [],
        },
        "legal_fact_map": [{
            "legal_element": "付款期限",
            "fact_ids": ["FACT-001"],
            "evidence_status": "合同已有记载",
        }],
    }


class ProcessingModesTest(unittest.TestCase):
    def test_report_mode_does_not_require_deferred_background_file_to_be_deep_read(self) -> None:
        result = validate_analysis_readiness(targeted_plan(), require_report=True)
        self.assertTrue(result.passed, result.errors)

    def test_fact_cannot_rely_on_unreviewed_material(self) -> None:
        plan = targeted_plan()
        plan["fact_inventory"][0]["source_material_ids"] = ["MAT-0002"]
        result = validate_analysis_readiness(plan, require_report=True)
        self.assertFalse(result.passed)
        self.assertTrue(any("尚未核对" in error for error in result.errors))

    def test_archive_mode_cannot_generate_analysis_outputs(self) -> None:
        result = validate_analysis_readiness(targeted_plan("archive"))
        self.assertFalse(result.passed)
        self.assertTrue(any("仅完成快速归档" in error for error in result.errors))

    def test_archive_plan_allows_recording_while_transcript_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            inventory = temp / "inventory.json"
            media_check = temp / "media-check.json"
            output = temp / "plan.json"
            inventory.write_text(json.dumps({
                "source_folder": str(temp),
                "files": [{
                    "original_name": "沟通录音.m4a",
                    "original_relative_path": "沟通录音.m4a",
                    "extension": ".m4a",
                    "sha256": "a" * 64,
                }],
            }, ensure_ascii=False), encoding="utf-8")
            media_check.write_text(json.dumps({
                "recording_count": 1,
                "ready_for_case_analysis": False,
                "requires_user_action": True,
            }, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPTS / "build_plan.py"), str(inventory),
                "--media-check", str(media_check), "--directory-mode", "default",
                "--processing-mode", "archive", "--out", str(output),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["processing_mode"], "archive")

    def test_mainline_plan_still_blocks_on_missing_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            inventory = temp / "inventory.json"
            media_check = temp / "media-check.json"
            inventory.write_text(json.dumps({
                "source_folder": str(temp),
                "files": [{
                    "original_name": "沟通录音.m4a",
                    "original_relative_path": "沟通录音.m4a",
                    "extension": ".m4a",
                    "sha256": "a" * 64,
                }],
            }, ensure_ascii=False), encoding="utf-8")
            media_check.write_text(json.dumps({
                "recording_count": 1,
                "ready_for_case_analysis": False,
            }, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPTS / "build_plan.py"), str(inventory),
                "--media-check", str(media_check), "--directory-mode", "default",
                "--processing-mode", "mainline", "--out", str(temp / "plan.json"),
            ], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("录音逐字稿检查尚未通过", result.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "lawyerbuddy-sorting" / "scripts" / "check_media.py"


def item(name: str, extension: str) -> dict:
    return {
        "original_name": name,
        "original_relative_path": name,
        "extension": extension,
    }


class MediaCheckTest(unittest.TestCase):
    def run_check(self, files: list[dict], confirms: list[str] | None = None) -> tuple[dict, dict]:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            inventory = base / "inventory.json"
            output = base / "media-check.json"
            inventory.write_text(
                json.dumps({"source_folder": "/case", "files": files}, ensure_ascii=False),
                encoding="utf-8",
            )
            command = [sys.executable, str(SCRIPT), str(inventory), "--out", str(output)]
            for pair in confirms or []:
                command.extend(["--confirm", pair])
            process = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(output.read_text(encoding="utf-8")), json.loads(process.stdout)

    def test_missing_transcript_exposes_tingwu_link(self) -> None:
        payload, stdout = self.run_check([item("220509-沟通录音.m4a", ".m4a")])
        self.assertFalse(payload["ready_for_case_analysis"])
        self.assertEqual(payload["transcription_service"], "https://tingwu.aliyun.com/home")
        self.assertIn("https://tingwu.aliyun.com/home", payload["next_action"])
        self.assertEqual(stdout["transcription_service"], "https://tingwu.aliyun.com/home")

    def test_same_date_recording_document_is_confirmation_candidate(self) -> None:
        payload, _ = self.run_check([
            item("【录音】20220509_161602.m4a", ".m4a"),
            item("20220509_161602(录音).docx", ".docx"),
        ])
        self.assertEqual(payload["missing_transcripts"], [])
        self.assertEqual(payload["ambiguous_matches"], ["【录音】20220509_161602.m4a"])
        self.assertEqual(
            payload["recordings"][0]["candidate_transcripts"],
            ["20220509_161602(录音).docx"],
        )

    def test_user_confirmation_unlocks_analysis(self) -> None:
        recording = "【证据材料】/【录音】20220509_161602.m4a"
        transcript = "【证据材料】/【录音】20220509_161602_原文.docx"
        payload, _ = self.run_check(
            [item(recording, ".m4a"), item(transcript, ".docx")],
            [f"{recording}={transcript}"],
        )
        self.assertTrue(payload["ready_for_case_analysis"])
        self.assertEqual(payload["recordings"][0]["matched_transcript"], transcript)
        self.assertTrue(payload["recordings"][0]["confirmed_by_user"])


if __name__ == "__main__":
    unittest.main()

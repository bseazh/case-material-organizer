from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SuiteStructureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "manifests" / "skills.json").read_text(encoding="utf-8")
        )

    def test_all_manifest_skills_have_matching_frontmatter(self) -> None:
        self.assertEqual(len(self.manifest["skills"]), 7)
        for skill in self.manifest["skills"]:
            skill_file = ROOT / "skills" / skill["name"] / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill["name"])
            text = skill_file.read_text(encoding="utf-8")
            self.assertIn(f"name: {skill['name']}", text)

    def test_ready_product_skills_are_declared(self) -> None:
        statuses = {skill["name"]: skill["status"] for skill in self.manifest["skills"]}
        self.assertEqual(statuses["lawyerbuddy"], "ready")
        self.assertEqual(statuses["lawyerbuddy-sorting"], "ready")
        self.assertEqual(statuses["lawyerbuddy-summarizing"], "ready")
        self.assertEqual(statuses["lawyerbuddy-timeline"], "ready")
        self.assertEqual(statuses["lawyerbuddy-similar-case-retrieval"], "planned")
        self.assertEqual(statuses["lawyerbuddy-document-drafting"], "planned")
        self.assertEqual(statuses["lawyerbuddy-contract-review"], "planned")

    def test_sorting_keeps_existing_runtime(self) -> None:
        sorting = ROOT / "skills" / "lawyerbuddy-sorting"
        required = [
            sorting / "assets" / "民事案件案由参考表_2025.xlsx",
            sorting / "scripts" / "build_plan.py",
            sorting / "scripts" / "build_report.py",
            sorting / "scripts" / "build_timeline.py",
            sorting / "references" / "interaction.md",
            sorting / "requirements.txt",
        ]
        for path in required:
            self.assertTrue(path.is_file(), str(path))

    def test_shared_contract_is_valid_json_schema_document(self) -> None:
        schema = json.loads(
            (ROOT / "runtime" / "contracts" / "case-data.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["type"], "object")
        self.assertIn("events", schema["required"])


if __name__ == "__main__":
    unittest.main()
